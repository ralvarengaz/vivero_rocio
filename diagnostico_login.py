import sqlite3
import hashlib

DB = "data/vivero.db"

def diagnosticar_login():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    print("🔍 DIAGNÓSTICO DE LOGIN")
    print("=" * 40)
    
    # Ver todos los usuarios
    cur.execute("SELECT id, username, password, nombre_completo, rol FROM usuarios")
    usuarios = cur.fetchall()
    
    print(f"👥 Usuarios en la base de datos:")
    for user in usuarios:
        user_id, username, password, nombre, rol = user
        print(f"   - ID: {user_id}")
        print(f"     Usuario: {username}")
        print(f"     Contraseña (hash): {password[:20]}...")
        print(f"     Nombre: {nombre}")
        print(f"     Rol: {rol}")
        print()
    
    # Verificar hash de contraseña para 'admin'
    password_admin = "admin123"
    hash_correcto = hashlib.sha256(password_admin.encode()).hexdigest()
    print(f"🔑 Hash correcto para 'admin123': {hash_correcto[:20]}...")
    
    # Verificar si coincide con algún usuario
    for user in usuarios:
        if user[1] == 'admin':
            print(f"📊 Usuario admin encontrado:")
            print(f"   Hash en DB: {user[2][:20]}...")
            print(f"   Hash esperado: {hash_correcto[:20]}...")
            print(f"   ¿Coincide? {'✅ SÍ' if user[2] == hash_correcto else '❌ NO'}")
    
    conn.close()

if __name__ == "__main__":
    diagnosticar_login()