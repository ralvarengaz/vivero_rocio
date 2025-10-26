"""
Sistema de migraciones incrementales y seguras para PostgreSQL
Reemplazo de migrations.py - NO hace DROP CASCADE en producción
"""
import os
from typing import List, Tuple
from modules.db_service import db
from modules.config import Modules


class Migration:
    """Clase base para migraciones"""

    def __init__(self, version: int, description: str):
        self.version = version
        self.description = description

    def up(self, conn):
        """Aplica la migración"""
        raise NotImplementedError

    def down(self, conn):
        """Revierte la migración"""
        raise NotImplementedError


class InitialMigration(Migration):
    """Migración inicial - Crea todas las tablas desde cero"""

    def __init__(self):
        super().__init__(1, "Crear esquema inicial de base de datos")

    def up(self, conn):
        cur = conn.cursor()

        # Tabla de control de migraciones
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                version INTEGER UNIQUE NOT NULL,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== TABLA USUARIOS ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                nombre_completo VARCHAR(100) NOT NULL,
                email VARCHAR(100),
                telefono VARCHAR(20),
                rol VARCHAR(20) DEFAULT 'Usuario' CHECK (rol IN ('Administrador', 'Gerente', 'Vendedor', 'Usuario')),
                estado VARCHAR(10) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_acceso TIMESTAMP,
                creado_por INTEGER,
                CONSTRAINT fk_usuarios_creado_por FOREIGN KEY (creado_por) REFERENCES usuarios(id) ON DELETE SET NULL
            )
        """)

        # Índices para usuarios
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(rol)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_estado ON usuarios(estado)")

        # ========== TABLA PERMISOS_USUARIO ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS permisos_usuario (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER NOT NULL,
                modulo VARCHAR(50) NOT NULL,
                puede_ver BOOLEAN DEFAULT false,
                puede_crear BOOLEAN DEFAULT false,
                puede_editar BOOLEAN DEFAULT false,
                puede_eliminar BOOLEAN DEFAULT false,
                UNIQUE(usuario_id, modulo),
                CONSTRAINT fk_permisos_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_permisos_usuario_id ON permisos_usuario(usuario_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_permisos_modulo ON permisos_usuario(modulo)")

        # ========== TABLA PRODUCTOS ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                categoria TEXT,
                unidad_medida TEXT DEFAULT 'Unidad',
                precio INTEGER DEFAULT 0,
                precio_compra INTEGER DEFAULT 0,
                precio_venta INTEGER DEFAULT 0,
                stock INTEGER DEFAULT 0,
                stock_minimo INTEGER DEFAULT 0,
                imagen TEXT,
                activo BOOLEAN DEFAULT true,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(nombre)
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_stock ON productos(stock)")

        # ========== TABLA CLIENTES ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                ruc TEXT,
                telefono TEXT,
                email TEXT,
                ciudad TEXT,
                direccion TEXT,
                activo BOOLEAN DEFAULT true,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clientes_ruc ON clientes(ruc)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clientes_activo ON clientes(activo)")

        # ========== TABLA PROVEEDORES ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                ruc TEXT,
                telefono TEXT,
                email TEXT,
                direccion TEXT,
                ciudad TEXT,
                activo BOOLEAN DEFAULT true,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_proveedores_nombre ON proveedores(nombre)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_proveedores_activo ON proveedores(activo)")

        # ========== TABLA CAJAS ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cajas (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL UNIQUE,
                ubicacion TEXT,
                estado TEXT DEFAULT 'Activa' CHECK (estado IN ('Activa', 'Inactiva')),
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== TABLA SESIONES_CAJA ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sesiones_caja (
                id SERIAL PRIMARY KEY,
                caja_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_cierre TIMESTAMP,
                monto_apertura INTEGER DEFAULT 0,
                monto_cierre INTEGER DEFAULT 0,
                estado TEXT DEFAULT 'Abierta' CHECK (estado IN ('Abierta', 'Cerrada')),
                observaciones TEXT,
                CONSTRAINT fk_sesiones_caja_caja FOREIGN KEY (caja_id) REFERENCES cajas(id) ON DELETE RESTRICT,
                CONSTRAINT fk_sesiones_caja_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_sesiones_usuario ON sesiones_caja(usuario_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sesiones_estado ON sesiones_caja(estado)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sesiones_fecha ON sesiones_caja(fecha_apertura)")

        # ========== TABLA VENTAS ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                numero_venta TEXT UNIQUE,
                sesion_caja_id INTEGER,
                cliente_id INTEGER,
                usuario_id INTEGER NOT NULL,
                fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subtotal INTEGER DEFAULT 0,
                descuento INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                monto_pagado INTEGER DEFAULT 0,
                vuelto INTEGER DEFAULT 0,
                metodo_pago TEXT DEFAULT 'Efectivo',
                estado TEXT DEFAULT 'Completada',
                observaciones TEXT,
                CONSTRAINT fk_ventas_sesion FOREIGN KEY (sesion_caja_id) REFERENCES sesiones_caja(id) ON DELETE SET NULL,
                CONSTRAINT fk_ventas_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
                CONSTRAINT fk_ventas_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_usuario ON ventas(usuario_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas(estado)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_numero ON ventas(numero_venta)")

        # ========== TABLA DETALLE_VENTAS ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id SERIAL PRIMARY KEY,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario INTEGER NOT NULL,
                subtotal INTEGER NOT NULL,
                CONSTRAINT fk_detalle_ventas_venta FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
                CONSTRAINT fk_detalle_ventas_producto FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_detalle_ventas_venta ON detalle_ventas(venta_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_detalle_ventas_producto ON detalle_ventas(producto_id)")

        # ========== TABLA PEDIDOS ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id SERIAL PRIMARY KEY,
                numero_pedido TEXT UNIQUE,
                cliente_id INTEGER,
                usuario_id INTEGER NOT NULL,
                destino TEXT,
                ubicacion TEXT,
                fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_entrega TIMESTAMP,
                estado TEXT DEFAULT 'Pendiente' CHECK (estado IN ('Pendiente', 'En Proceso', 'Entregado', 'Cancelado')),
                costo_delivery INTEGER DEFAULT 0,
                subtotal INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                observaciones TEXT,
                CONSTRAINT fk_pedidos_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
                CONSTRAINT fk_pedidos_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_fecha ON pedidos(fecha_pedido)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos(cliente_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_numero ON pedidos(numero_pedido)")

        # ========== TABLA DETALLE_PEDIDO ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS detalle_pedido (
                id SERIAL PRIMARY KEY,
                pedido_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario INTEGER NOT NULL,
                subtotal INTEGER NOT NULL,
                CONSTRAINT fk_detalle_pedido_pedido FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
                CONSTRAINT fk_detalle_pedido_producto FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_detalle_pedido_pedido ON detalle_pedido(pedido_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_detalle_pedido_producto ON detalle_pedido(producto_id)")

        print("✅ Esquema de base de datos creado exitosamente")


    def down(self, conn):
        """Revierte la migración inicial"""
        cur = conn.cursor()

        # Eliminar tablas en orden inverso
        tables = [
            'detalle_pedido',
            'detalle_ventas',
            'pedidos',
            'ventas',
            'sesiones_caja',
            'cajas',
            'permisos_usuario',
            'proveedores',
            'clientes',
            'productos',
            'usuarios',
            'schema_migrations'
        ]

        for table in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

        print("✅ Esquema de base de datos eliminado")


class CreateDefaultDataMigration(Migration):
    """Migración 2 - Crea datos por defecto (admin, caja principal)"""

    def __init__(self):
        super().__init__(2, "Crear datos por defecto (admin, caja)")

    def up(self, conn):
        import bcrypt
        cur = conn.cursor()

        # Verificar si ya existe el admin
        cur.execute("SELECT id FROM usuarios WHERE username = 'admin'")
        if cur.fetchone():
            print("⚠️ Usuario admin ya existe, omitiendo creación")
            return

        # Crear usuario administrador con bcrypt
        password = "admin123"
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        cur.execute("""
            INSERT INTO usuarios (username, password, nombre_completo, email, rol, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, ('admin', password_hash, 'Administrador del Sistema', 'admin@vivero.com', 'Administrador', 'Activo'))

        admin_id = cur.fetchone()[0]

        # Permisos completos para administrador
        modulos = Modules.ALL
        for modulo in modulos:
            cur.execute("""
                INSERT INTO permisos_usuario (usuario_id, modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
                VALUES (%s, %s, true, true, true, true)
                ON CONFLICT (usuario_id, modulo) DO NOTHING
            """, (admin_id, modulo))

        # Crear caja principal
        cur.execute("""
            INSERT INTO cajas (nombre, ubicacion, estado)
            VALUES (%s, %s, %s)
            ON CONFLICT (nombre) DO NOTHING
        """, ('Caja Principal', 'Sucursal Principal', 'Activa'))

        print("✅ Datos por defecto creados (admin/admin123, Caja Principal)")

    def down(self, conn):
        cur = conn.cursor()
        cur.execute("DELETE FROM usuarios WHERE username = 'admin'")
        cur.execute("DELETE FROM cajas WHERE nombre = 'Caja Principal'")
        print("✅ Datos por defecto eliminados")


# Lista de todas las migraciones
MIGRATIONS: List[Migration] = [
    InitialMigration(),
    CreateDefaultDataMigration(),
]


def get_current_version(conn) -> int:
    """Obtiene la versión actual de la base de datos"""
    cur = conn.cursor()
    try:
        cur.execute("SELECT MAX(version) FROM schema_migrations")
        result = cur.fetchone()
        return result[0] if result and result[0] else 0
    except:
        return 0


def apply_migrations(force_recreate: bool = False):
    """
    Aplica migraciones pendientes

    Args:
        force_recreate: Si es True, elimina y recrea todo (SOLO DESARROLLO)
    """
    # Verificar si estamos en producción
    is_production = os.environ.get("DATABASE_URL", "").startswith("postgres")

    if force_recreate and is_production:
        print("❌ ERROR: No se puede usar force_recreate en producción")
        print("❌ Esto eliminaría TODOS los datos de la base de datos")
        return

    with db.get_connection() as conn:
        try:
            if force_recreate:
                print("⚠️ ADVERTENCIA: Eliminando y recreando base de datos...")
                print("⚠️ TODOS los datos serán eliminados")

                # Ejecutar down de todas las migraciones en orden inverso
                for migration in reversed(MIGRATIONS):
                    migration.down(conn)
                    print(f"⬇️ Revertida: {migration.description}")

            # Obtener versión actual
            current_version = get_current_version(conn)
            print(f"📊 Versión actual de BD: {current_version}")

            # Aplicar migraciones pendientes
            for migration in MIGRATIONS:
                if migration.version > current_version:
                    print(f"⬆️ Aplicando migración {migration.version}: {migration.description}")
                    migration.up(conn)

                    # Registrar migración aplicada
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO schema_migrations (version, description)
                        VALUES (%s, %s)
                        ON CONFLICT (version) DO NOTHING
                    """, (migration.version, migration.description))

                    print(f"✅ Migración {migration.version} aplicada exitosamente")

            conn.commit()
            print("✅ Todas las migraciones aplicadas exitosamente")

        except Exception as e:
            conn.rollback()
            print(f"❌ Error aplicando migraciones: {e}")
            import traceback
            traceback.print_exc()
            raise


def ensure_schema(db_url: str = None, force_recreate: bool = False):
    """
    Función de compatibilidad con migrations.py anterior
    Asegura que el esquema de BD esté actualizado

    Args:
        db_url: URL de la base de datos (ignorado, usa config)
        force_recreate: Si debe recrear la BD desde cero (SOLO DESARROLLO)
    """
    apply_migrations(force_recreate=force_recreate)
