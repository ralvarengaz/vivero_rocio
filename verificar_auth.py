import sqlite3
import hashlib

DB = "data/vivero.db"

def verificar_autenticacion(username, password):
    """Simula el proceso de login"""
    print(f"🔐 Verificando login para: {username}")
    
    # Hashear la contraseña ingresada
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    print(f"🔑 Hash de contraseña ingresada: {password_hash[:20]}...")
    
    # Buscar en la base de datos
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    cur.execute("SELECT id, password, rol, estado FROM usuarios WHERE username = ?", (username,))
    usuario = cur.fetchone()
    
    if not usuario:
        print("❌ Usuario no encontrado")
        return False
    
    user_id, db_password, rol, estado = usuario
    print(f"🔍 Hash en base de datos: {db_password[:20]}...")
    print(f"👤 Rol: {rol}")
    print(f"📊 Estado: {estado}")
    
    if db_password == password_hash:
        if estado == 'Activo':
            print("✅ Login exitoso")
            return True
        else:
            print("❌ Usuario inactivo")
            return False
    else:
        print("❌ Contraseña incorrecta")
        return False
    
    conn.close()

if __name__ == "__main__":
    # Test con credenciales admin
    print("=" * 50)
    print("PRUEBA DE AUTENTICACIÓN")
    print("=" * 50)
    
    resultado = verificar_autenticacion("admin", "admin123")
    print(f"\n🎯 Resultado final: {'ÉXITO' if resultado else 'FALLO'}")