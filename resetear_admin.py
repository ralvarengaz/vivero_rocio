import sqlite3
import hashlib

DB = "data/vivero.db"

def resetear_password_admin():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Nueva contraseña hasheada
    nueva_password = "admin123"
    password_hash = hashlib.sha256(nueva_password.encode()).hexdigest()
    
    print("🔄 Reseteando contraseña del administrador...")
    
    # Actualizar contraseña del admin
    cur.execute("""
        UPDATE usuarios 
        SET password = ? 
        WHERE username = 'admin'
    """, (password_hash,))
    
    if cur.rowcount > 0:
        print("✅ Contraseña del admin actualizada")
        print(f"🔑 Usuario: admin")
        print(f"🔑 Contraseña: {nueva_password}")
        print(f"🔐 Hash: {password_hash}")
    else:
        print("❌ Usuario admin no encontrado")
        
        # Crear usuario admin si no existe
        print("🔄 Creando usuario admin...")
        cur.execute("""
            INSERT INTO usuarios (username, password, nombre_completo, email, rol, estado, creado_por)
            VALUES ('admin', ?, 'Administrador del Sistema', 'admin@vivero.com', 'Administrador', 'Activo', 1)
        """, (password_hash,))
        
        admin_id = cur.lastrowid
        print(f"✅ Usuario admin creado con ID: {admin_id}")
        
        # Asignar permisos completos
        modulos = ['productos', 'clientes', 'proveedores', 'pedidos', 'ventas', 'reportes', 'usuarios']
        for modulo in modulos:
            cur.execute("""
                INSERT OR REPLACE INTO permisos_usuario 
                (usuario_id, modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
                VALUES (?, ?, 1, 1, 1, 1)
            """, (admin_id, modulo))
        
        print("🛡️ Permisos completos asignados")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Proceso completado")
    print("💡 Credenciales de acceso:")
    print("   Usuario: admin")
    print("   Contraseña: admin123")

if __name__ == "__main__":
    resetear_password_admin()