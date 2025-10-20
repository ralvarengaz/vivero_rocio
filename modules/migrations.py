import os
import psycopg2

def ensure_schema(db_url):
    """
    Crea el esquema completo de la base de datos PostgreSQL
    Compatible con todas las funcionalidades del sistema
    """
    try:
        con = psycopg2.connect(db_url)
        cur = con.cursor()

        print("🔄 Creando esquema de base de datos PostgreSQL...")

        # ========== TABLA USUARIOS - Con migración de estructura antigua ==========
        # Verificar si existe una tabla usuarios con estructura antigua (sin username)
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'usuarios' AND column_name = 'username'
        """)
        username_exists = cur.fetchone()
        
        # Si la tabla existe pero no tiene la columna username, necesita ser migrada
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'usuarios'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if table_exists and not username_exists:
            print("⚠️ Detectada tabla usuarios con estructura antigua. Migrando...")
            # Respaldar datos existentes si los hay
            cur.execute("SELECT COUNT(*) FROM usuarios")
            user_count = cur.fetchone()[0]
            
            if user_count > 0:
                print(f"📦 Respaldando {user_count} usuarios...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios_backup AS 
                    SELECT * FROM usuarios
                """)
            
            # Eliminar tabla antigua
            print("🗑️ Eliminando tabla usuarios antigua...")
            cur.execute("DROP TABLE IF EXISTS usuarios CASCADE")
            print("✅ Tabla antigua eliminada")
        
        # Crear tabla usuarios con estructura correcta
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
        
        # Verificar que la columna username existe antes de crear índices
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'usuarios' AND column_name = 'username'
        """)
        if cur.fetchone():
            # Índices para usuarios
            cur.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(rol);")
        else:
            print("⚠️ No se pudo crear índice en username: columna no encontrada")
        
        # ========== TABLA PERMISOS_USUARIO ==========
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
        
        # ========== TABLA PRODUCTOS ==========
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
        
        # ========== TABLA CLIENTES ==========
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
        
        # ========== TABLA PROVEEDORES ==========
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
        
        # ========== TABLA CAJAS ==========
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cajas (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL UNIQUE,
            ubicacion TEXT,
            estado TEXT DEFAULT 'Activa' CHECK (estado IN ('Activa', 'Inactiva'))
        );
        """)
        
        # ========== TABLA SESIONES_CAJA ==========
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
        
        # ========== TABLA VENTAS ==========
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
        
        # ========== TABLA DETALLE_VENTAS ==========
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
        
        # ========== TABLA PEDIDOS ==========
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
        
        # ========== TABLA DETALLE_PEDIDO ==========
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
        
        # ========== USUARIO ADMINISTRADOR POR DEFECTO ==========
        print("👤 Verificando usuario administrador...")
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
        admin_exists = cur.fetchone()[0]
        
        if admin_exists == 0:
            print("🔧 Creando usuario administrador por defecto...")
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
                    ON CONFLICT (usuario_id, modulo) DO NOTHING
                """, (admin_id, modulo))
            
            print("✅ Usuario administrador creado (username: admin, password: admin123)")
        else:
            print("ℹ️ Usuario administrador ya existe")
        
        # ========== CAJA POR DEFECTO ==========
        cur.execute("SELECT COUNT(*) FROM cajas WHERE nombre = 'Caja Principal'")
        caja_exists = cur.fetchone()[0]
        
        if caja_exists == 0:
            print("🏦 Creando caja principal por defecto...")
            cur.execute("""
                INSERT INTO cajas (nombre, ubicacion, estado)
                VALUES ('Caja Principal', 'Sucursal Principal', 'Activa')
            """)
            print("✅ Caja principal creada")
        
        con.commit()
        cur.close()
        con.close()
        
        print("✅ Base PostgreSQL inicializada correctamente.")
        print("📊 Tablas creadas: usuarios, permisos_usuario, productos, clientes,")
        print("   proveedores, cajas, sesiones_caja, ventas, detalle_ventas,")
        print("   pedidos, detalle_pedido")

    except Exception as e:
        print(f"🚨 Error en ensure_schema(): {e}")
        import traceback
        traceback.print_exc()
        raise
