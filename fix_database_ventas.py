import sqlite3

DB = "data/vivero.db"

def fix_database_structure():
    """Corrige la estructura de la base de datos para el módulo de ventas"""
    print("🔧 Corrigiendo estructura de la base de datos...")
    
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    try:
        # ===== TABLA VENTAS =====
        print("📋 Verificando tabla ventas...")
        
        # Verificar columnas existentes
        cur.execute("PRAGMA table_info(ventas)")
        columnas_ventas = [col[1] for col in cur.fetchall()]
        print(f"Columnas actuales en ventas: {columnas_ventas}")
        
        # Agregar columnas faltantes
        columnas_requeridas = [
            ('usuario_id', 'INTEGER'),
            ('numero_venta', 'TEXT'),
            ('sesion_caja_id', 'INTEGER'),
            ('subtotal', 'DECIMAL(15,0) DEFAULT 0'),
            ('descuento', 'DECIMAL(15,0) DEFAULT 0'),
            ('monto_pagado', 'DECIMAL(15,0) DEFAULT 0'),
            ('vuelto', 'DECIMAL(15,0) DEFAULT 0'),
            ('metodo_pago', 'TEXT DEFAULT "Efectivo"'),
        ]
        
        for columna, tipo in columnas_requeridas:
            if columna not in columnas_ventas:
                print(f"➕ Agregando columna '{columna}' a ventas...")
                try:
                    cur.execute(f"ALTER TABLE ventas ADD COLUMN {columna} {tipo}")
                except Exception as e:
                    print(f"⚠️ Error agregando {columna}: {e}")
        
        # ===== TABLA CLIENTES =====
        print("📋 Verificando tabla clientes...")
        
        # Verificar columnas existentes
        cur.execute("PRAGMA table_info(clientes)")
        columnas_clientes = [col[1] for col in cur.fetchall()]
        print(f"Columnas actuales en clientes: {columnas_clientes}")
        
        # Agregar columnas faltantes
        columnas_clientes_req = [
            ('email', 'TEXT'),
            ('direccion', 'TEXT'),
        ]
        
        for columna, tipo in columnas_clientes_req:
            if columna not in columnas_clientes:
                print(f"➕ Agregando columna '{columna}' a clientes...")
                try:
                    cur.execute(f"ALTER TABLE clientes ADD COLUMN {columna} {tipo}")
                except Exception as e:
                    print(f"⚠️ Error agregando {columna}: {e}")
        
        # ===== TABLA USUARIOS =====
        print("📋 Verificando tabla usuarios...")
        
        # Verificar columnas existentes
        cur.execute("PRAGMA table_info(usuarios)")
        columnas_usuarios = [col[1] for col in cur.fetchall()]
        print(f"Columnas actuales en usuarios: {columnas_usuarios}")
        
        # Agregar columna faltante si no existe
        if 'nombre_completo' not in columnas_usuarios:
            print("➕ Agregando columna 'nombre_completo' a usuarios...")
            try:
                cur.execute("ALTER TABLE usuarios ADD COLUMN nombre_completo TEXT")
            except Exception as e:
                print(f"⚠️ Error agregando nombre_completo: {e}")
        
        # ===== ACTUALIZAR DATOS EXISTENTES =====
        print("🔄 Actualizando datos existentes...")
        
        # Asegurar que todos los usuarios tengan nombre_completo
        cur.execute("""
            UPDATE usuarios 
            SET nombre_completo = COALESCE(nombre_completo, nombre, username) 
            WHERE nombre_completo IS NULL OR nombre_completo = ''
        """)
        
        # Actualizar ventas sin usuario_id
        cur.execute("""
            UPDATE ventas 
            SET usuario_id = 1 
            WHERE usuario_id IS NULL
        """)
        
        # Actualizar ventas sin numero_venta
        cur.execute("""
            UPDATE ventas 
            SET numero_venta = 'V' || DATE('now', 'localtime') || id
            WHERE numero_venta IS NULL OR numero_venta = ''
        """)
        
        # Commit cambios
        conn.commit()
        print("✅ Base de datos actualizada correctamente")
        
        # ===== VERIFICAR CAMBIOS =====
        print("\n🔍 Verificando cambios...")
        
        # Verificar ventas
        cur.execute("SELECT COUNT(*) FROM ventas")
        total_ventas = cur.fetchone()[0]
        print(f"📊 Total de ventas en BD: {total_ventas}")
        
        # Verificar clientes
        cur.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = cur.fetchone()[0]
        print(f"👥 Total de clientes en BD: {total_clientes}")
        
        # Verificar usuarios
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE nombre_completo IS NOT NULL")
        usuarios_completos = cur.fetchone()[0]
        print(f"👨‍💼 Usuarios con nombre completo: {usuarios_completos}")
        
    except Exception as e:
        print(f"❌ Error actualizando BD: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

def insertar_datos_ejemplo():
    """Inserta datos de ejemplo si las tablas están vacías"""
    print("\n📝 Verificando datos de ejemplo...")
    
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    try:
        # Verificar si hay clientes
        cur.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = cur.fetchone()[0]
        
        if total_clientes < 2:  # Solo Cliente General existe
            print("👥 Insertando clientes de ejemplo...")
            clientes_ejemplo = [
                ("María González", "0981-123-456", "maria.gonzalez@email.com", "Asunción, Paraguay"),
                ("Juan Pérez", "0985-789-012", "juan.perez@email.com", "Luque, Paraguay"),
                ("Ana Silva", "0991-345-678", "ana.silva@email.com", "San Lorenzo, Paraguay"),
                ("Carlos Rodríguez", "0971-234-567", "carlos.rodriguez@email.com", "Fernando de la Mora"),
            ]
            
            for cliente in clientes_ejemplo:
                try:
                    cur.execute("""
                        INSERT INTO clientes (nombre, telefono, email, direccion, estado)
                        VALUES (?, ?, ?, ?, 'Activo')
                    """, cliente)
                except Exception as e:
                    print(f"⚠️ Error insertando cliente {cliente[0]}: {e}")
            
            print("✅ Clientes de ejemplo insertados")
        else:
            print(f"ℹ️ Ya existen {total_clientes} clientes en la BD")
        
        # Verificar estructura final
        print("\n📋 Estructura final de tablas:")
        
        # Ventas
        cur.execute("PRAGMA table_info(ventas)")
        cols_ventas = [col[1] for col in cur.fetchall()]
        print(f"💰 Ventas ({len(cols_ventas)} columnas): {cols_ventas}")
        
        # Clientes
        cur.execute("PRAGMA table_info(clientes)")
        cols_clientes = [col[1] for col in cur.fetchall()]
        print(f"👥 Clientes ({len(cols_clientes)} columnas): {cols_clientes}")
        
        # Usuarios
        cur.execute("PRAGMA table_info(usuarios)")
        cols_usuarios = [col[1] for col in cur.fetchall()]
        print(f"👨‍💼 Usuarios ({len(cols_usuarios)} columnas): {cols_usuarios}")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error insertando datos: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando corrección de base de datos para módulo de ventas...")
    print("=" * 60)
    fix_database_structure()
    insertar_datos_ejemplo()
    print("=" * 60)
    print("🎉 Corrección completada!")
    print("\n💡 Ahora puede ejecutar 'python main.py' para usar el PdV completo")