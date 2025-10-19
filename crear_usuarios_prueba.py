import sqlite3
import hashlib

DB = "data/vivero.db"

def crear_usuarios_prueba():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    print("🔧 Creando usuarios de prueba...")
    
    # Lista de usuarios a crear
    usuarios_prueba = [
        {
            'username': 'vendedor',
            'password': 'vendedor123',
            'nombre_completo': 'Juan Vendedor',
            'email': 'vendedor@vivero.com',
            'rol': 'Vendedor',
            'permisos': {
                'productos': {'ver': 1, 'crear': 0, 'editar': 0, 'eliminar': 0},  # Solo ver
                'clientes': {'ver': 1, 'crear': 1, 'editar': 1, 'eliminar': 0},   # Gestionar sin eliminar
                'ventas': {'ver': 1, 'crear': 1, 'editar': 0, 'eliminar': 0},     # Crear y ver ventas
                'pedidos': {'ver': 1, 'crear': 1, 'editar': 1, 'eliminar': 0},    # Gestionar pedidos
                'reportes': {'ver': 1, 'crear': 0, 'editar': 0, 'eliminar': 0},   # Solo ver reportes
                # Sin acceso a: proveedores, usuarios
            }
        },
        {
            'username': 'gerente',
            'password': 'gerente123',
            'nombre_completo': 'María Gerente',
            'email': 'gerente@vivero.com',
            'rol': 'Gerente',
            'permisos': {
                'productos': {'ver': 1, 'crear': 1, 'editar': 1, 'eliminar': 0},   # Gestión completa sin eliminar
                'clientes': {'ver': 1, 'crear': 1, 'editar': 1, 'eliminar': 1},    # Acceso completo
                'proveedores': {'ver': 1, 'crear': 1, 'editar': 1, 'eliminar': 0}, # Gestión sin eliminar
                'pedidos': {'ver': 1, 'crear': 1, 'editar': 1, 'eliminar': 1},     # Acceso completo
                'ventas': {'ver': 1, 'crear': 1, 'editar': 1, 'eliminar': 0},      # Gestión sin eliminar
                'reportes': {'ver': 1, 'crear': 1, 'editar': 0, 'eliminar': 0},    # Ver y generar reportes
                # Sin acceso a: usuarios
            }
        },
        {
            'username': 'usuario',
            'password': 'usuario123',
            'nombre_completo': 'Carlos Usuario',
            'email': 'usuario@vivero.com',
            'rol': 'Usuario',
            'permisos': {
                'productos': {'ver': 1, 'crear': 0, 'editar': 0, 'eliminar': 0},   # Solo consultar
                'clientes': {'ver': 1, 'crear': 0, 'editar': 0, 'eliminar': 0},    # Solo consultar
                'reportes': {'ver': 1, 'crear': 0, 'editar': 0, 'eliminar': 0},    # Solo ver reportes básicos
                # Sin acceso a: proveedores, pedidos, ventas, usuarios
            }
        },
        {
            'username': 'inactivo',
            'password': 'inactivo123',
            'nombre_completo': 'Usuario Inactivo',
            'email': 'inactivo@vivero.com',
            'rol': 'Usuario',
            'estado': 'Inactivo'  # Este usuario está deshabilitado
        }
    ]
    
    for usuario_data in usuarios_prueba:
        username = usuario_data['username']
        
        # Verificar si el usuario ya existe
        cur.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        existing = cur.fetchone()
        
        if existing:
            print(f"⚠️  Usuario '{username}' ya existe, actualizando...")
            usuario_id = existing[0]
            
            # Actualizar usuario existente
            password_hash = hashlib.sha256(usuario_data['password'].encode()).hexdigest()
            cur.execute("""
                UPDATE usuarios 
                SET password=?, nombre_completo=?, email=?, rol=?, estado=?
                WHERE id=?
            """, (
                password_hash,
                usuario_data['nombre_completo'],
                usuario_data.get('email', ''),
                usuario_data['rol'],
                usuario_data.get('estado', 'Activo'),
                usuario_id
            ))
        else:
            # Crear nuevo usuario
            password_hash = hashlib.sha256(usuario_data['password'].encode()).hexdigest()
            cur.execute("""
                INSERT INTO usuarios (username, password, nombre_completo, email, rol, estado, creado_por)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                username,
                password_hash,
                usuario_data['nombre_completo'],
                usuario_data.get('email', ''),
                usuario_data['rol'],
                usuario_data.get('estado', 'Activo')
            ))
            usuario_id = cur.lastrowid
            print(f"✅ Usuario '{username}' creado")
        
        # Configurar permisos (solo si tiene permisos definidos)
        if 'permisos' in usuario_data:
            # Limpiar permisos existentes
            cur.execute("DELETE FROM permisos_usuario WHERE usuario_id = ?", (usuario_id,))
            
            # Insertar nuevos permisos
            for modulo, permisos in usuario_data['permisos'].items():
                cur.execute("""
                    INSERT INTO permisos_usuario (usuario_id, modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    usuario_id,
                    modulo,
                    permisos['ver'],
                    permisos['crear'],
                    permisos['editar'],
                    permisos['eliminar']
                ))
            
            print(f"   🔐 Permisos configurados: {len(usuario_data['permisos'])} módulos")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 ¡Usuarios de prueba creados exitosamente!")
    print("\n" + "="*60)
    print("📋 CREDENCIALES DE USUARIOS DE PRUEBA:")
    print("="*60)
    print("👑 ADMINISTRADOR (Acceso Total):")
    print("   Usuario: admin")
    print("   Contraseña: admin123")
    print("   Permisos: Todos los módulos con acceso completo")
    
    print("\n🏢 GERENTE (Acceso Amplio):")
    print("   Usuario: gerente")
    print("   Contraseña: gerente123")
    print("   Permisos: Productos, Clientes, Proveedores, Pedidos, Ventas, Reportes")
    print("   Restricciones: No puede eliminar productos/proveedores/ventas, no acceso a usuarios")
    
    print("\n💼 VENDEDOR (Acceso Operativo):")
    print("   Usuario: vendedor") 
    print("   Contraseña: vendedor123")
    print("   Permisos: Ver productos, gestionar clientes/ventas/pedidos, ver reportes")
    print("   Restricciones: No puede modificar productos, no acceso a proveedores/usuarios")
    
    print("\n👤 USUARIO (Solo Consulta):")
    print("   Usuario: usuario")
    print("   Contraseña: usuario123")
    print("   Permisos: Solo consultar productos, clientes y reportes básicos")
    print("   Restricciones: No puede crear/editar/eliminar nada")
    
    print("\n🚫 USUARIO INACTIVO (Sin Acceso):")
    print("   Usuario: inactivo")
    print("   Contraseña: inactivo123")
    print("   Estado: Deshabilitado - No puede iniciar sesión")
    
    print("\n" + "="*60)

def mostrar_permisos_detallados():
    """Muestra una tabla detallada de permisos por usuario"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    print("\n📊 TABLA DETALLADA DE PERMISOS:")
    print("="*80)
    
    # Obtener usuarios y sus permisos
    cur.execute("""
        SELECT u.username, u.rol, u.estado, p.modulo, p.puede_ver, p.puede_crear, p.puede_editar, p.puede_eliminar
        FROM usuarios u
        LEFT JOIN permisos_usuario p ON u.id = p.usuario_id
        WHERE u.username IN ('admin', 'gerente', 'vendedor', 'usuario', 'inactivo')
        ORDER BY u.username, p.modulo
    """)
    
    results = cur.fetchall()
    current_user = None
    
    for row in results:
        username, rol, estado, modulo, ver, crear, editar, eliminar = row
        
        if username != current_user:
            print(f"\n👤 {username.upper()} ({rol}) - Estado: {estado}")
            print("-" * 50)
            current_user = username
        
        if modulo:
            acciones = []
            if ver: acciones.append("Ver")
            if crear: acciones.append("Crear") 
            if editar: acciones.append("Editar")
            if eliminar: acciones.append("Eliminar")
            
            acciones_str = ", ".join(acciones) if acciones else "Sin permisos"
            print(f"   📁 {modulo:<12} → {acciones_str}")
        else:
            if rol == 'Administrador':
                print("   🔓 ACCESO TOTAL A TODOS LOS MÓDULOS")
            else:
                print("   ❌ Sin permisos configurados")
    
    conn.close()
    print("\n" + "="*80)

if __name__ == "__main__":
    crear_usuarios_prueba()
    mostrar_permisos_detallados()