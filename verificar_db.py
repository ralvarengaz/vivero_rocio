import sqlite3

DB = "data/vivero.db"

def verificar_base_datos():
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        # Listar todas las tablas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cur.fetchall()
        print("Tablas en la base de datos:")
        for tabla in tablas:
            print(f"  - {tabla[0]}")
        
        # Verificar si existe tabla usuarios
        if ('usuarios',) in tablas:
            cur.execute("PRAGMA table_info(usuarios)")
            columnas = cur.fetchall()
            print(f"\nEstructura de tabla usuarios:")
            for col in columnas:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("❌ Tabla usuarios no existe")
        
        # Verificar si existe tabla permisos_usuario
        if ('permisos_usuario',) in tablas:
            cur.execute("PRAGMA table_info(permisos_usuario)")
            columnas = cur.fetchall()
            print(f"\nEstructura de tabla permisos_usuario:")
            for col in columnas:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("❌ Tabla permisos_usuario no existe")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verificar_base_datos()