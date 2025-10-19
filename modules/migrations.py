import os
import psycopg2

def ensure_schema(db_url):
    try:
        con = psycopg2.connect(db_url)
        cur = con.cursor()

        # Tabla usuarios COMPLETA
        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            usuario VARCHAR(50) UNIQUE NOT NULL,  -- Compatibilidad
            password VARCHAR(255) NOT NULL,
            nombre_completo VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            telefono VARCHAR(20),
            rol VARCHAR(20) DEFAULT 'Usuario',
            estado VARCHAR(10) DEFAULT 'Activo',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultimo_acceso TIMESTAMP,
            creado_por INTEGER
        );
        
        -- Crear usuario admin por defecto
        INSERT INTO usuarios (username, usuario, password, nombre_completo, rol, estado)
        VALUES ('admin', 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 
                'Administrador del Sistema', 'Administrador', 'Activo')
        ON CONFLICT (username) DO NOTHING;
        
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
            imagen TEXT
        );
        
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            ruc TEXT,
            telefono TEXT,
            email TEXT,
            correo TEXT,
            ciudad TEXT,
            ubicacion TEXT,
            direccion TEXT
        );
        
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
            estado TEXT DEFAULT 'Completada'
        );
        
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id SERIAL PRIMARY KEY,
            venta_id INTEGER REFERENCES ventas(id) ON DELETE CASCADE,
            producto_id INTEGER REFERENCES productos(id) ON DELETE RESTRICT,
            cantidad INTEGER NOT NULL,
            precio_unitario INTEGER NOT NULL,
            subtotal INTEGER NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS pedidos (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER REFERENCES clientes(id),
            destino TEXT,
            ubicacion TEXT,
            fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_entrega TIMESTAMP,
            estado TEXT DEFAULT 'Pendiente',
            costo_delivery INTEGER DEFAULT 0,
            costo_total INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS detalle_pedido (
            id SERIAL PRIMARY KEY,
            pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
            producto_id INTEGER REFERENCES productos(id),
            cantidad INTEGER NOT NULL,
            precio_unitario INTEGER NOT NULL,
            subtotal INTEGER NOT NULL
        );
        """)

        con.commit()
        cur.close()
        con.close()
        print("✅ Base PostgreSQL inicializada correctamente.")

    except Exception as e:
        print(f"🚨 Error en ensure_schema(): {e}")
