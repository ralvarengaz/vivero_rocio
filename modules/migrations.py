import os
import sqlite3

def ensure_schema(db_path):
    """
    Crea el archivo de base de datos y las tablas necesarias si no existen.
    Compatible con Render (usa /tmp).
    """
    try:
        # Crear el directorio antes de abrir la conexión
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"📁 Carpeta creada: {db_dir}")

        con = sqlite3.connect(db_path)
        con.execute("PRAGMA foreign_keys=ON;")

        con.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'vendedor'
        );

        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT,
            unidad TEXT,
            precio_compra INTEGER DEFAULT 0,
            precio_venta INTEGER DEFAULT 0,
            imagen TEXT
        );

        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            total INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario INTEGER NOT NULL,
            subtotal INTEGER NOT NULL,
            FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT
        );
        """)

        con.commit()
        con.close()
        print(f"✅ Base de datos inicializada correctamente en {db_path}")

    except Exception as e:
        print(f"🚨 Error en ensure_schema(): {e}")
