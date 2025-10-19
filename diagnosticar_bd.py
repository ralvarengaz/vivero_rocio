import sqlite3

DB = "data/vivero.db"

def diagnosticar_bd():
    """Diagnostica problemas en la base de datos"""
    print("🔍 === DIAGNÓSTICO DE BASE DE DATOS ===\n")
    
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # 1. Verificar todas las tablas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = cur.fetchall()
    print(f"📋 Tablas encontradas: {[t[0] for t in tablas]}\n")
    
    # 2. Verificar estructura de cada tabla importante
    tablas_importantes = ['productos', 'ventas', 'sesiones_caja', 'cajas']
    
    for tabla in tablas_importantes:
        try:
            cur.execute(f"PRAGMA table_info({tabla})")
            columnas = cur.fetchall()
            print(f"🔧 Tabla '{tabla}':")
            for col in columnas:
                print(f"   - {col[1]} ({col[2]})")
            
            # Contar registros
            cur.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cur.fetchone()[0]
            print(f"   📊 Total registros: {count}\n")
            
        except Exception as e:
            print(f"❌ Error con tabla '{tabla}': {e}\n")
    
    # 3. Verificar productos específicamente
    try:
        cur.execute("SELECT id, nombre, precio, stock FROM productos LIMIT 5")
        productos = cur.fetchall()
        print("🛍️ Muestra de productos:")
        for p in productos:
            print(f"   - ID: {p[0]}, Nombre: {p[1]}, Precio: {p[2]}, Stock: {p[3]}")
        print()
    except Exception as e:
        print(f"❌ Error consultando productos: {e}\n")
    
    # 4. Verificar sesiones de caja
    try:
        cur.execute("SELECT id, usuario_id, estado, monto_apertura FROM sesiones_caja")
        sesiones = cur.fetchall()
        print("📦 Sesiones de caja:")
        for s in sesiones:
            print(f"   - ID: {s[0]}, Usuario: {s[1]}, Estado: {s[2]}, Monto: {s[3]}")
        print()
    except Exception as e:
        print(f"❌ Error consultando sesiones: {e}\n")
    
    conn.close()
    print("✅ Diagnóstico completado")

if __name__ == "__main__":
    diagnosticar_bd()