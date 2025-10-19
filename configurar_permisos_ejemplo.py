import sqlite3

DB = "data/vivero.db"

def configurar_permisos_vendedor():
    """Configura permisos específicos para rol Vendedor"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Buscar o crear usuario vendedor de ejemplo
    cur.execute("SELECT id FROM usuarios WHERE rol = 'Vendedor' LIMIT 1")
    vendedor = cur.fetchone()
    
    if not vendedor:
        # Crear usuario vendedor de ejemplo
        import hashlib
        password_hash = hashlib.sha256("vendedor123".encode()).hexdigest()
        cur.execute("""
            INSERT INTO usuarios (username, password, nombre_completo, email, rol, estado, creado_por)
            VALUES ('vendedor', ?, 'Juan Vendedor', 'vendedor@vivero.com', 'Vendedor', 'Activo', 1)
        """, (password_hash,))
        vendedor_id = cur.lastrowid
    else:
        vendedor_id = vendedor[0]
    
    # Limpiar permisos existentes
    cur.execute("DELETE FROM permisos_usuario WHERE usuario_id = ?", (vendedor_id,))
    
    # Configurar permisos específicos para vendedor
    permisos_vendedor = {
        'productos': {'ver': 1, 'crear': 0, 'editar': 0, 'eliminar': 0},  # Solo ver productos
        'clientes': {'ver': 1, 'crear': 1, 'editar': 1, 'eliminar': 0},   # Gestionar clientes (sin eliminar)
        'ventas': {'ver': 1, 'crear': 1, 'editar': 0, 'eliminar': 0},     # Crear ventas, ver historial
        'pedidos': {'ver': 1, 'crear': 1, 'editar': 1, 'eliminar': 0},    # Gestionar pedidos
        'reportes': {'ver': 1, 'crear': 0, 'editar': 0, 'eliminar': 0},   # Solo ver reportes básicos
        # Sin acceso a: proveedores, usuarios
    }
    
    for modulo, permisos in permisos_vendedor.items():
        cur.execute("""
            INSERT INTO permisos_usuario (usuario_id, modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vendedor_id, modulo, permisos['ver'], permisos['crear'], permisos['editar'], permisos['eliminar']))
    
    conn.commit()
    conn.close()
    
    print("✅ Permisos configurados para usuario vendedor")
    print("🔑 Credenciales: vendedor / vendedor123")
    print("📋 Accesos:")
    for modulo, permisos in permisos_vendedor.items():
        acciones = [k for k, v in permisos.items() if v]
        print(f"   - {modulo}: {', '.join(acciones)}")

if __name__ == "__main__":
    configurar_permisos_vendedor()