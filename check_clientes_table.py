import sqlite3

DB = "data/vivero.db"

def verificar_tabla_clientes():
    """Verifica la estructura de la tabla clientes"""
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        print("📋 ESTRUCTURA DE LA TABLA CLIENTES")
        print("=" * 40)
        
        # Verificar estructura
        cur.execute("PRAGMA table_info(clientes)")
        columnas = cur.fetchall()
        
        print("Columnas existentes:")
        for col in columnas:
            print(f"  - {col[1]:15} {col[2]:10} {'NOT NULL' if col[3] else 'NULL'}")
        
        # Mostrar algunos registros
        print(f"\n📊 DATOS DE EJEMPLO")
        print("-" * 30)
        
        cur.execute("SELECT * FROM clientes LIMIT 3")
        registros = cur.fetchall()
        
        if registros:
            for reg in registros:
                print(f"ID: {reg[0]}, Nombre: {reg[1]}, RUC: {reg[2] if len(reg) > 2 else 'N/A'}")
        else:
            print("No hay registros en la tabla")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_tabla_clientes()