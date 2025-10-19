import os
import psycopg2

def ensure_schema(db_url):
    try:
        con = psycopg2.connect(db_url)
        cur = con.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario TEXT NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'vendedor'
        );
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            categoria TEXT,
            unidad TEXT,
            precio_compra INTEGER DEFAULT 0,
            precio_venta INTEGER DEFAULT 0,
            imagen TEXT
        );
        CREATE TABLE IF NOT EXISTS ventas (
            id SERIAL PRIMARY KEY,
            cliente TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id SERIAL PRIMARY KEY,
            venta_id INTEGER REFERENCES ventas(id) ON DELETE CASCADE,
            producto_id INTEGER REFERENCES productos(id) ON DELETE RESTRICT,
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
