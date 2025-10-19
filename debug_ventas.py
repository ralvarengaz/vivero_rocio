# Agrega este script para debugging
import sqlite3
from session_manager import session

DB = "data/vivero.db"

def debug_ventas():
    print("🐛 === DEBUG VENTAS ===")
    
    # Verificar usuario actual
    current_user = session.get_current_user()
    print(f"Usuario actual: {current_user}")
    
    # Verificar conexión BD
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        # Verificar tablas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%caja%'")
        tablas = cur.fetchall()
        print(f"Tablas de caja: {tablas}")
        
        # Verificar cajas
        cur.execute("SELECT * FROM cajas")
        cajas = cur.fetchall()
        print(f"Cajas existentes: {cajas}")
        
        # Verificar sesiones
        cur.execute("SELECT * FROM sesiones_caja")
        sesiones = cur.fetchall()
        print(f"Sesiones existentes: {sesiones}")
        
        conn.close()
        print("✅ Conexión BD exitosa")
        
    except Exception as e:
        print(f"❌ Error BD: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ventas()