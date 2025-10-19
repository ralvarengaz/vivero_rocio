import sqlite3

DB = "data/vivero.db"

def migrar_tabla_usuarios():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    print("🔄 Migrando tabla usuarios...")
    
    # 1. Hacer backup de usuarios actuales
    cur.execute("SELECT * FROM usuarios")
    usuarios_existentes = cur.fetchall()
    print(f"📊 Encontrados {len(usuarios_existentes)} usuarios existentes")
    
    # 2. Crear nueva tabla usuarios con estructura completa
    cur.execute("DROP TABLE IF EXISTS usuarios_backup")
    cur.execute("CREATE TABLE usuarios_backup AS SELECT * FROM usuarios")
    print("✅ Backup de usuarios creado")
    
    # 3. Eliminar tabla usuarios actual
    cur.execute("DROP TABLE usuarios")
    
    # 4. Crear nueva tabla usuarios
    cur.execute('''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            nombre_completo VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            telefono VARCHAR(20),
            rol VARCHAR(20) DEFAULT 'Usuario' CHECK (rol IN ('Administrador', 'Gerente', 'Vendedor', 'Usuario')),
            estado VARCHAR(10) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultimo_acceso DATETIME,
            creado_por INTEGER,
            FOREIGN KEY (creado_por) REFERENCES usuarios(id)
        )
    ''')
    print("✅ Nueva tabla usuarios creada")
    
    # 5. Migrar datos existentes
    for usuario in usuarios_existentes:
        user_id, username, password, role, rol = usuario
        
        # Determinar rol correcto
        rol_final = rol if rol in ['Administrador', 'Gerente', 'Vendedor', 'Usuario'] else 'Usuario'
        if not rol_final and role:
            rol_final = role if role in ['Administrador', 'Gerente', 'Vendedor', 'Usuario'] else 'Usuario'
        
        # Generar nombre completo basado en username
        nombre_completo = f"Usuario {username.capitalize()}"
        if username == 'admin':
            nombre_completo = "Administrador del Sistema"
        
        cur.execute('''
            INSERT INTO usuarios (id, username, password, nombre_completo, rol, estado, creado_por)
            VALUES (?, ?, ?, ?, ?, 'Activo', 1)
        ''', (user_id, username, password, nombre_completo, rol_final))
    
    print(f"✅ {len(usuarios_existentes)} usuarios migrados")
    
    # 6. Crear tabla permisos si no existe
    cur.execute('''
        CREATE TABLE IF NOT EXISTS permisos_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            modulo VARCHAR(50) NOT NULL,
            puede_ver BOOLEAN DEFAULT 0,
            puede_crear BOOLEAN DEFAULT 0,
            puede_editar BOOLEAN DEFAULT 0,
            puede_eliminar BOOLEAN DEFAULT 0,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            UNIQUE(usuario_id, modulo)
        )
    ''')
    
    # 7. Asignar permisos a usuarios existentes
    modulos = ['productos', 'clientes', 'proveedores', 'pedidos', 'ventas', 'reportes', 'usuarios']
    
    for usuario in usuarios_existentes:
        user_id = usuario[0]
        rol_usuario = usuario[4] if len(usuario) > 4 else usuario[3]  # rol o role
        
        # Permisos según rol
        if rol_usuario == 'Administrador':
            permisos = {'ver': 1, 'crear': 1, 'editar': 1, 'eliminar': 1}
        elif rol_usuario == 'Gerente':
            permisos = {'ver': 1, 'crear': 1, 'editar': 1, 'eliminar': 0}
        elif rol_usuario == 'Vendedor':
            permisos = {'ver': 1, 'crear': 1, 'editar': 0, 'eliminar': 0}
        else:
            permisos = {'ver': 1, 'crear': 0, 'editar': 0, 'eliminar': 0}
        
        for modulo in modulos:
            # Solo administradores pueden gestionar usuarios
            if modulo == 'usuarios' and rol_usuario != 'Administrador':
                cur.execute('''
                    INSERT OR IGNORE INTO permisos_usuario (usuario_id, modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
                    VALUES (?, ?, 0, 0, 0, 0)
                ''', (user_id, modulo))
            else:
                cur.execute('''
                    INSERT OR IGNORE INTO permisos_usuario (usuario_id, modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, modulo, permisos['ver'], permisos['crear'], permisos['editar'], permisos['eliminar']))
    
    print(f"✅ Permisos asignados para {len(modulos)} módulos")
    
    conn.commit()
    conn.close()
    
    print("🎉 Migración completada exitosamente")
    print("📋 Usuarios migrados con nuevos campos:")
    print("   - nombre_completo, email, telefono, estado, fecha_creacion")
    print("🔐 Permisos asignados según roles existentes")

def verificar_migracion():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    print("\n🔍 Verificando migración...")
    
    # Verificar estructura usuarios
    cur.execute("PRAGMA table_info(usuarios)")
    columnas = cur.fetchall()
    print("📊 Nuevas columnas en usuarios:")
    for col in columnas:
        print(f"   - {col[1]} ({col[2]})")
    
    # Contar usuarios
    cur.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = cur.fetchone()[0]
    
    # Contar permisos
    cur.execute("SELECT COUNT(*) FROM permisos_usuario")
    total_permisos = cur.fetchone()[0]
    
    print(f"\n📈 Estadísticas:")
    print(f"   - Total usuarios: {total_usuarios}")
    print(f"   - Total permisos: {total_permisos}")
    
    # Mostrar usuarios migrados
    cur.execute("SELECT username, nombre_completo, rol, estado FROM usuarios")
    usuarios = cur.fetchall()
    print(f"\n👥 Usuarios migrados:")
    for user in usuarios:
        print(f"   - {user[0]} ({user[1]}) - {user[2]} - {user[3]}")
    
    conn.close()

if __name__ == "__main__":
    migrar_tabla_usuarios()
    verificar_migracion()