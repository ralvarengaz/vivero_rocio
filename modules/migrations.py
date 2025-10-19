
import sqlite3

def ensure_schema(db_path):
    con = sqlite3.connect(db_path)
    try:
        con.execute("PRAGMA foreign_keys=ON;")
        con.executescript("\n-- Normalización de tablas de ventas\nCREATE TABLE IF NOT EXISTS ventas (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    cliente_id INTEGER,\n    fecha TEXT NOT NULL DEFAULT (DATE('now')),\n    total INTEGER NOT NULL DEFAULT 0,\n    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL ON UPDATE CASCADE\n);\nCREATE TABLE IF NOT EXISTS detalle_ventas (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    venta_id INTEGER NOT NULL,\n    producto_id INTEGER NOT NULL,\n    cantidad INTEGER NOT NULL,\n    precio_unitario INTEGER NOT NULL,\n    subtotal INTEGER NOT NULL,\n    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE ON UPDATE CASCADE,\n    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT ON UPDATE CASCADE\n);\n")
        con.commit()
    finally:
        con.close()
