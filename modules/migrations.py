import os
import time
import psycopg2

def ensure_schema(db_url):
    """
    Crea el esquema completo de la base de datos PostgreSQL
    Compatible con todas las funcionalidades del sistema
    """
    try:
        con = psycopg2.connect(db_url)
        cur = con.cursor()

        print("🔄 Recreando esquema completo de base de datos PostgreSQL...")
        print("⚠️ ADVERTENCIA: Se eliminarán TODAS las tablas y datos existentes")
        
        # ========== DROP ALL EXISTING TABLES ==========
        # Drop tables in correct order to avoid foreign key conflicts
        # (reverse order of creation - detail tables first, then parent tables)
        # Nota: Orden explícito requerido por especificación del problema.
        # CASCADE garantiza eliminación de todas las dependencias.
        print("\n🗑️ Eliminando tablas existentes...")
        
        print("   Eliminando detalle_pedido...")
        cur.execute("DROP TABLE IF EXISTS detalle_pedido CASCADE;")
        
        print("   Eliminando detalle_ventas...")
        cur.execute("DROP TABLE IF EXISTS detalle_ventas CASCADE;")
        
        print("   Eliminando pedidos...")
        cur.execute("DROP TABLE IF EXISTS pedidos CASCADE;")
        
        print("   Eliminando ventas...")
        cur.execute("DROP TABLE IF EXISTS ventas CASCADE;")
        
        print("   Eliminando sesiones_caja...")
        cur.execute("DROP TABLE IF EXISTS sesiones_caja CASCADE;")
        
        print("   Eliminando cajas...")
        cur.execute("DROP TABLE IF EXISTS cajas CASCADE;")
        
        print("   Eliminando permisos_usuario...")
        cur.execute("DROP TABLE IF EXISTS permisos_usuario CASCADE;")
        
        print("   Eliminando proveedores...")
        cur.execute("DROP TABLE IF EXISTS proveedores CASCADE;")
        
        print("   Eliminando clientes...")
        cur.execute("DROP TABLE IF EXISTS clientes CASCADE;")
        
        print("   Eliminando productos...")
        cur.execute("DROP TABLE IF EXISTS productos CASCADE;")
        
        print("   Eliminando usuarios...")
        cur.execute("DROP TABLE IF EXISTS usuarios CASCADE;")
        
        print("✅ Todas las tablas eliminadas exitosamente\n")
        print("🔨 Creando tablas nuevas con estructura correcta...")
        
        # ========== TABLA USUARIOS ==========
        print("\n   Creando tabla: usuarios")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            usuario VARCHAR(50),  -- Compatibilidad con código legacy
            password VARCHAR(255) NOT NULL,
            nombre_completo VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            telefono VARCHAR(20),
            rol VARCHAR(20) DEFAULT 'Usuario' CHECK (rol IN ('Administrador', 'Gerente', 'Vendedor', 'Usuario')),
            estado VARCHAR(10) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultimo_acceso TIMESTAMP,
            creado_por INTEGER
        );
        """)
        
        # Índices para usuarios
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(rol);")
        print("   ✅ Tabla usuarios creada")
        
        # ========== TABLA PERMISOS_USUARIO ==========
        print("   Creando tabla: permisos_usuario")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS permisos_usuario (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            modulo VARCHAR(50) NOT NULL,
            puede_ver BOOLEAN DEFAULT false,
            puede_crear BOOLEAN DEFAULT false,
            puede_editar BOOLEAN DEFAULT false,
            puede_eliminar BOOLEAN DEFAULT false,
            UNIQUE(usuario_id, modulo)
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_permisos_usuario_id ON permisos_usuario(usuario_id);")
        print("   ✅ Tabla permisos_usuario creada")
        
        # ========== TABLA PRODUCTOS ==========
        print("   Creando tabla: productos")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            categoria TEXT,
            unidad TEXT,
            unidad_medida TEXT,
            precio INTEGER DEFAULT 0,
            precio_compra INTEGER DEFAULT 0,
            precio_venta INTEGER DEFAULT 0,
            stock INTEGER DEFAULT 0,
            imagen TEXT,
            UNIQUE(nombre)
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria);")
        print("   ✅ Tabla productos creada")
        
        # ========== TABLA CLIENTES ==========
        print("   Creando tabla: clientes")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            ruc TEXT,
            ruc_ci TEXT,  -- Compatibilidad
            telefono TEXT,
            tel TEXT,     -- Compatibilidad
            email TEXT,
            correo TEXT,  -- Compatibilidad
            ciudad TEXT,
            ubicacion TEXT,
            direccion TEXT
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre);")
        print("   ✅ Tabla clientes creada")
        
        # ========== TABLA PROVEEDORES ==========
        print("   Creando tabla: proveedores")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            ruc TEXT,
            telefono TEXT,
            email TEXT,
            direccion TEXT,
            ciudad TEXT
        );
        """)
        print("   ✅ Tabla proveedores creada")
        
        # ========== TABLA CAJAS ==========
        print("   Creando tabla: cajas")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cajas (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL UNIQUE,
            ubicacion TEXT,
            estado TEXT DEFAULT 'Activa' CHECK (estado IN ('Activa', 'Inactiva'))
        );
        """)
        print("   ✅ Tabla cajas creada")
        
        # ========== TABLA SESIONES_CAJA ==========
        print("   Creando tabla: sesiones_caja")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sesiones_caja (
            id SERIAL PRIMARY KEY,
            caja_id INTEGER REFERENCES cajas(id),
            usuario_id INTEGER REFERENCES usuarios(id),
            fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_cierre TIMESTAMP,
            monto_apertura INTEGER DEFAULT 0,
            monto_cierre INTEGER DEFAULT 0,
            estado TEXT DEFAULT 'Abierta' CHECK (estado IN ('Abierta', 'Cerrada'))
        );
        """)
        print("   ✅ Tabla sesiones_caja creada")
        
        # ========== TABLA VENTAS ==========
        print("   Creando tabla: ventas")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id SERIAL PRIMARY KEY,
            numero_venta TEXT UNIQUE,
            sesion_caja_id INTEGER REFERENCES sesiones_caja(id),
            cliente_id INTEGER REFERENCES clientes(id),
            usuario_id INTEGER REFERENCES usuarios(id),
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subtotal INTEGER DEFAULT 0,
            descuento INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            monto_pagado INTEGER DEFAULT 0,
            vuelto INTEGER DEFAULT 0,
            metodo_pago TEXT DEFAULT 'Efectivo',
            estado TEXT DEFAULT 'Completada',
            observaciones TEXT
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_usuario ON ventas(usuario_id);")
        print("   ✅ Tabla ventas creada")
        
        # ========== TABLA DETALLE_VENTAS ==========
        print("   Creando tabla: detalle_ventas")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id SERIAL PRIMARY KEY,
            venta_id INTEGER REFERENCES ventas(id) ON DELETE CASCADE,
            producto_id INTEGER REFERENCES productos(id) ON DELETE RESTRICT,
            cantidad INTEGER NOT NULL,
            precio_unitario INTEGER NOT NULL,
            subtotal INTEGER NOT NULL
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_detalle_ventas_venta ON detalle_ventas(venta_id);")
        print("   ✅ Tabla detalle_ventas creada")
        
        # ========== TABLA PEDIDOS ==========
        print("   Creando tabla: pedidos")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER REFERENCES clientes(id),
            usuario_id INTEGER REFERENCES usuarios(id),
            destino TEXT,
            ubicacion TEXT,
            fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_entrega TIMESTAMP,
            estado TEXT DEFAULT 'Pendiente' CHECK (estado IN ('Pendiente', 'En Proceso', 'Entregado', 'Cancelado')),
            costo_delivery INTEGER DEFAULT 0,
            costo_total INTEGER DEFAULT 0,
            observaciones TEXT
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_fecha ON pedidos(fecha_pedido);")
        print("   ✅ Tabla pedidos creada")
        
        # ========== TABLA DETALLE_PEDIDO ==========
        print("   Creando tabla: detalle_pedido")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS detalle_pedido (
            id SERIAL PRIMARY KEY,
            pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
            producto_id INTEGER REFERENCES productos(id),
            cantidad INTEGER NOT NULL,
            precio_unitario INTEGER NOT NULL,
            subtotal INTEGER NOT NULL
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_detalle_pedido_pedido ON detalle_pedido(pedido_id);")
        print("   ✅ Tabla detalle_pedido creada")
        
        # ========== DATOS INICIALES ==========
        # Nota: No necesitamos ON CONFLICT porque todas las tablas fueron eliminadas
        # y recreadas vacías. Estos INSERT son seguros en este contexto.
        
        # ========== USUARIO ADMINISTRADOR POR DEFECTO ==========
        print("\n👤 Creando usuario administrador por defecto...")
        # Contraseña: admin123 (SHA256)
        password_hash = '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9'
        
        cur.execute("""
            INSERT INTO usuarios (username, usuario, password, nombre_completo, email, rol, estado, creado_por)
            VALUES ('admin', 'admin', %s, 'Administrador del Sistema', 'admin@vivero.com', 'Administrador', 'Activo', NULL)
        """, (password_hash,))
        
        cur.execute("SELECT id FROM usuarios WHERE username = 'admin'")
        admin_id = cur.fetchone()[0]
        
        # Permisos completos para administrador
        modulos = ['productos', 'clientes', 'proveedores', 'pedidos', 'ventas', 'reportes', 'usuarios']
        for modulo in modulos:
            cur.execute("""
                INSERT INTO permisos_usuario (usuario_id, modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
                VALUES (%s, %s, true, true, true, true)
            """, (admin_id, modulo))
        
        print("✅ Usuario administrador creado (username: admin, password: admin123)")
        
        # ========== CAJA POR DEFECTO ==========
        print("🏦 Creando caja principal por defecto...")
        cur.execute("""
            INSERT INTO cajas (nombre, ubicacion, estado)
            VALUES ('Caja Principal', 'Sucursal Principal', 'Activa')
        """)
        print("✅ Caja principal creada")
        
        con.commit()
        cur.close()
        con.close()
        
        print("\n✅ Base PostgreSQL recreada exitosamente.")
        print("📊 Tablas creadas: usuarios, permisos_usuario, productos, clientes,")
        print("   proveedores, cajas, sesiones_caja, ventas, detalle_ventas,")
        print("   pedidos, detalle_pedido")
        print("🔐 Usuario admin disponible con todas las credenciales")

    except Exception as e:
        print(f"🚨 Error en ensure_schema(): {e}")
        import traceback
        traceback.print_exc()
        raise
