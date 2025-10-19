import sqlite3
import os

DB = "data/vivero.db"

def crear_tablas_usuarios():
    # Crear directorio data si no existe
    if not os.path.exists("data"):
        os.makedirs("data")
    
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Verificar si las tablas ya existen
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
    tabla_usuarios_existe = cur.fetchone()
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='permisos_usuario'")
    tabla_permisos_existe = cur.fetchone()
    
    # Crear tabla usuarios si no existe
    if not tabla_usuarios_existe:
        print("Creando tabla usuarios...")
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
        print("✅ Tabla usuarios creada")
    else:
        print("ℹ️ Tabla usuarios ya existe")
    
    # Crear tabla permisos si no existe
    if not tabla_permisos_existe:
        print("Creando tabla permisos_usuario...")
        cur.execute('''
            CREATE TABLE permisos_usuario (
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
        print("✅ Tabla permisos_usuario creada")
    else:
        print("ℹ️ Tabla permisos_usuario ya existe")
    
    # Verificar si existe usuario admin
    cur.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
    admin_existe = cur.fetchone()[0] > 0
    
    if not admin_existe:
        print("Creando usuario administrador...")
        # Contraseña hasheada de 'admin123'
        password_hash = '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9'
        
        cur.execute('''
            INSERT INTO usuarios (username, password, nombre_completo, email, rol, estado, creado_por) 
            VALUES ('admin', ?, 'Administrador del Sistema', 'admin@vivero.com', 'Administrador', 'Activo', 1)
        ''', (password_hash,))
        
        admin_id = cur.lastrowid
        
        # Permisos completos para el administrador
        modulos = ['productos', 'clientes', 'proveedores', 'pedidos', 'ventas', 'reportes', 'usuarios']
        for modulo in modulos:
            cur.execute('''
                INSERT INTO permisos_usuario (usuario_id, modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
                VALUES (?, ?, 1, 1, 1, 1)
            ''', (admin_id, modulo))
        
        print("✅ Usuario administrador creado")
        print("🔑 Credenciales - Usuario: admin | Contraseña: admin123")
    else:
        print("ℹ️ Usuario administrador ya existe")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Configuración de usuarios completada correctamente")
    print("📊 Puedes acceder al CRUD de usuarios desde el dashboard")

def verificar_tablas():
    """Verifica que las tablas estén creadas correctamente"""
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        # Verificar estructura de tabla usuarios
        cur.execute("PRAGMA table_info(usuarios)")
        columnas_usuarios = cur.fetchall()
        print("Columnas en tabla usuarios:")
        for col in columnas_usuarios:
            print(f"  - {col[1]} ({col[2]})")
        
        # Contar usuarios
        cur.execute("SELECT COUNT(*) FROM usuarios")
        total_usuarios = cur.fetchone()[0]
        print(f"\nTotal de usuarios: {total_usuarios}")
        
        # Verificar estructura de tabla permisos
        cur.execute("PRAGMA table_info(permisos_usuario)")
        columnas_permisos = cur.fetchall()
        print("\nColumnas en tabla permisos_usuario:")
        for col in columnas_permisos:
            print(f"  - {col[1]} ({col[2]})")
        
        # Contar permisos
        cur.execute("SELECT COUNT(*) FROM permisos_usuario")
        total_permisos = cur.fetchone()[0]
        print(f"\nTotal de permisos: {total_permisos}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar tablas: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Configurando sistema de usuarios...")
    crear_tablas_usuarios()
    print("\n🔍 Verificando configuración...")
    verificar_tablas()