import os
import psycopg2

def ensure_schema(db_url):
    """Crea todas las tablas necesarias en PostgreSQL"""
    try:
        con = psycopg2.connect(db_url)
        cur = con.cursor()
        
        print("🔄 Ejecutando migraciones...")

        # ==================== TABLA USUARIOS ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            usuario VARCHAR(50) UNIQUE,
            password VARCHAR(255) NOT NULL,
            nombre_completo VARCHAR(100) NOT NULL DEFAULT 'Usuario',
            email VARCHAR(100),
            telefono VARCHAR(20),
            rol VARCHAR(20) DEFAULT 'Usuario' CHECK (rol IN ('Administrador', 'Gerente', 'Vendedor', 'Usuario')),
            estado VARCHAR(10) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultimo_acceso TIMESTAMP,
            creado_por INTEGER
        );
        """)
        
        # Crear usuario admin por defecto (contraseña: admin123)
        cur.execute("""
        INSERT INTO usuarios (username, usuario, password, nombre_completo, email, rol, estado)
        VALUES ('admin', 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 
                'Administrador del Sistema', 'admin@vivero.com', 'Administrador', 'Activo')
        ON CONFLICT (username) DO NOTHING;
        """)
        
        print("✅ Tabla usuarios creada/verificada")

        # ==================== TABLA PERMISOS ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS permisos_usuario (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            modulo VARCHAR(50) NOT NULL,
            puede_ver BOOLEAN DEFAULT FALSE,
            puede_crear BOOLEAN DEFAULT FALSE,
            puede_editar BOOLEAN DEFAULT FALSE,
            puede_eliminar BOOLEAN DEFAULT FALSE,
            UNIQUE(usuario_id, modulo)
        );
        """)
        
        # Permisos completos para admin
        modulos = ['productos', 'clientes', 'proveedores', 'pedidos', 'ventas', 'reportes', 'usuarios']
        for modulo in modulos:
            cur.execute("""
            INSERT INTO permisos_usuario (usuario_id, modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
            SELECT 1, %s, TRUE, TRUE, TRUE, TRUE
            WHERE NOT EXISTS (
                SELECT 1 FROM permisos_usuario WHERE usuario_id = 1 AND modulo = %s
            );
            """, (modulo, modulo))
        
        print("✅ Tabla permisos_usuario creada/verificada")

        # ==================== TABLA PRODUCTOS ====================
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
            descripcion TEXT,
            codigo_barras TEXT,
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("✅ Tabla productos creada/verificada")

        # ==================== TABLA CLIENTES ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            ruc TEXT,
            telefono TEXT,
            email TEXT,
            correo TEXT,
            ciudad TEXT,
            ubicacion TEXT,
            direccion TEXT,
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Cliente general por defecto
        cur.execute("""
        INSERT INTO clientes (nombre, telefono, ciudad)
        VALUES ('Cliente General', '', 'Asunción')
        ON CONFLICT DO NOTHING;
        """)
        
        print("✅ Tabla clientes creada/verificada")

        # ==================== TABLA PROVEEDORES ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            ruc TEXT,
            telefono TEXT,
            email TEXT,
            direccion TEXT,
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("✅ Tabla proveedores creada/verificada")

        # ==================== TABLA VENTAS ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id SERIAL PRIMARY KEY,
            numero_venta TEXT UNIQUE,
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
            observaciones TEXT,
            sesion_caja_id INTEGER
        );
        """)
        print("✅ Tabla ventas creada/verificada")

        # ==================== TABLA DETALLE VENTAS ====================
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
        print("✅ Tabla detalle_ventas creada/verificada")

        # ==================== TABLA PEDIDOS ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER REFERENCES clientes(id),
            usuario_id INTEGER REFERENCES usuarios(id),
            destino TEXT,
            ubicacion TEXT,
            fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_entrega TIMESTAMP,
            estado TEXT DEFAULT 'Pendiente',
            costo_delivery INTEGER DEFAULT 0,
            costo_total INTEGER DEFAULT 0,
            observaciones TEXT
        );
        """)
        print("✅ Tabla pedidos creada/verificada")

        # ==================== TABLA DETALLE PEDIDOS ====================
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
        print("✅ Tabla detalle_pedido creada/verificada")

        # ==================== TABLA CAJAS ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cajas (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Caja principal por defecto
        cur.execute("""
        INSERT INTO cajas (nombre, descripcion, activo)
        VALUES ('Caja Principal', 'Caja de ventas principal', TRUE)
        ON CONFLICT DO NOTHING;
        """)
        
        print("✅ Tabla cajas creada/verificada")

        # ==================== TABLA SESIONES CAJA ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sesiones_caja (
            id SERIAL PRIMARY KEY,
            caja_id INTEGER REFERENCES cajas(id),
            usuario_id INTEGER REFERENCES usuarios(id),
            monto_apertura INTEGER DEFAULT 0,
            monto_cierre INTEGER DEFAULT 0,
            fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_cierre TIMESTAMP,
            estado TEXT DEFAULT 'Abierta' CHECK (estado IN ('Abierta', 'Cerrada')),
            observaciones TEXT
        );
        """)
        print("✅ Tabla sesiones_caja creada/verificada")

        # ==================== ÍNDICES PARA PERFORMANCE ====================
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta);
        CREATE INDEX IF NOT EXISTS idx_ventas_usuario ON ventas(usuario_id);
        CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id);
        CREATE INDEX IF NOT EXISTS idx_detalle_ventas_venta ON detalle_ventas(venta_id);
        CREATE INDEX IF NOT EXISTS idx_pedidos_fecha ON pedidos(fecha_pedido);
        CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado);
        """)
        print("✅ Índices creados/verificados")

        con.commit()
        cur.close()
        con.close()
        
        print("=" * 50)
        print("✅ Base PostgreSQL inicializada correctamente.")
        print("🔑 Usuario admin creado: admin / admin123")
        print("=" * 50)

    except Exception as e:
        print(f"🚨 Error en ensure_schema(): {e}")
        import traceback
        traceback.print_exc()
        raise
