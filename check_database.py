import sqlite3
import os

DB = "data/vivero.db"

def verificar_estructura():
    """Verifica la estructura actual de la base de datos"""
    print("🔍 VERIFICANDO ESTRUCTURA DE LA BASE DE DATOS")
    print("=" * 50)
    
    if not os.path.exists(DB):
        print("❌ Base de datos no existe")
        return
    
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        # Obtener todas las tablas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cur.fetchall()
        
        print(f"📊 Tablas encontradas: {len(tablas)}")
        
        for tabla in tablas:
            nombre_tabla = tabla[0]
            print(f"\n📋 TABLA: {nombre_tabla}")
            print("-" * 30)
            
            # Obtener estructura de la tabla
            cur.execute(f"PRAGMA table_info({nombre_tabla})")
            columnas = cur.fetchall()
            
            for col in columnas:
                print(f"  {col[1]:20} {col[2]:10} {'NOT NULL' if col[3] else 'NULL':8} {f'DEFAULT {col[4]}' if col[4] else ''}")
            
            # Contar registros
            cur.execute(f"SELECT COUNT(*) FROM {nombre_tabla}")
            count = cur.fetchone()[0]
            print(f"  📊 Registros: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_estructura()