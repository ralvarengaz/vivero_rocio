import sqlite3
import os
from datetime import datetime

DB = "data/vivero.db"

def verificar_y_actualizar_bd():
    """Verifica y actualiza la estructura de la base de datos"""
    print("🔍 Verificando estructura de la base de datos...")
    
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📁 Directorio 'data' creado")
    
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        # === VERIFICAR TABLA PRODUCTOS ===
        print("\n📦 Verificando tabla productos...")
        cur.execute("PRAGMA table_info(productos)")
        columnas_productos = cur.fetchall()
        
        if not columnas_productos:
            print("❌ Tabla productos no existe, creándola...")
            cur.execute("""
                CREATE TABLE productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    categoria TEXT NOT NULL,
                    unidad_medida TEXT DEFAULT 'Unitario',
                    unidad TEXT DEFAULT 'Unitario',
                    precio_compra REAL DEFAULT 0,
                    precio_venta REAL DEFAULT 0,
                    precio REAL DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    fecha_creacion TEXT DEFAULT '2025-01-01 00:00:00',
                    fecha_actualizacion TEXT DEFAULT '2025-01-01 00:00:00'
                )
            """)
            print("✅ Tabla productos creada")
        else:
            print("✅ Tabla productos existe")
            print("   Columnas actuales:")
            for col in columnas_productos:
                print(f"     - {col[1]} ({col[2]})")
            
            # Verificar y agregar columnas faltantes
            columnas_existentes = [col[1] for col in columnas_productos]
            
            if 'stock' not in columnas_existentes:
                print("   📋 Agregando columna 'stock'...")
                cur.execute("ALTER TABLE productos ADD COLUMN stock INTEGER DEFAULT 0")
                print("   ✅ Columna 'stock' agregada")
            
            if 'unidad_medida' not in columnas_existentes:
                print("   📋 Agregando columna 'unidad_medida'...")
                cur.execute("ALTER TABLE productos ADD COLUMN unidad_medida TEXT DEFAULT 'Unitario'")
                print("   ✅ Columna 'unidad_medida' agregada")
            
            if 'fecha_creacion' not in columnas_existentes:
                print("   📋 Agregando columna 'fecha_creacion'...")
                cur.execute("ALTER TABLE productos ADD COLUMN fecha_creacion TEXT DEFAULT '2025-01-01 00:00:00'")
                
                # Actualizar registros existentes con la fecha actual
                fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("UPDATE productos SET fecha_creacion = ? WHERE fecha_creacion = '2025-01-01 00:00:00'", (fecha_actual,))
                print("   ✅ Columna 'fecha_creacion' agregada y actualizada")
            
            if 'fecha_actualizacion' not in columnas_existentes:
                print("   📋 Agregando columna 'fecha_actualizacion'...")
                cur.execute("ALTER TABLE productos ADD COLUMN fecha_actualizacion TEXT DEFAULT '2025-01-01 00:00:00'")
                
                # Actualizar registros existentes
                fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("UPDATE productos SET fecha_actualizacion = ? WHERE fecha_actualizacion = '2025-01-01 00:00:00'", (fecha_actual,))
                print("   ✅ Columna 'fecha_actualizacion' agregada y actualizada")
        
        # === VERIFICAR TABLA CLIENTES ===
        print("\n👥 Verificando tabla clientes...")
        cur.execute("PRAGMA table_info(clientes)")
        columnas_clientes = cur.fetchall()
        
        if not columnas_clientes:
            print("❌ Tabla clientes no existe, creándola...")
            cur.execute("""
                CREATE TABLE clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT,
                    correo TEXT,
                    direccion TEXT,
                    ubicacion TEXT,
                    fecha_creacion TEXT DEFAULT '2025-01-01 00:00:00'
                )
            """)
            print("✅ Tabla clientes creada")
        else:
            print("✅ Tabla clientes existe")
            print("   Columnas actuales:")
            for col in columnas_clientes:
                print(f"     - {col[1]} ({col[2]})")
            
            # Verificar y agregar columnas faltantes en clientes
            columnas_clientes_existentes = [col[1] for col in columnas_clientes]
            
            if 'fecha_creacion' not in columnas_clientes_existentes:
                print("   📋 Agregando columna 'fecha_creacion' a clientes...")
                cur.execute("ALTER TABLE clientes ADD COLUMN fecha_creacion TEXT DEFAULT '2025-01-01 00:00:00'")
                
                # Actualizar registros existentes
                fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("UPDATE clientes SET fecha_creacion = ? WHERE fecha_creacion = '2025-01-01 00:00:00'", (fecha_actual,))
                print("   ✅ Columna 'fecha_creacion' agregada a clientes")
        
        # Ahora verificar si existe Cliente General (después de agregar columnas)
        cur.execute("SELECT id FROM clientes WHERE nombre = 'Cliente General'")
        if not cur.fetchone():
            print("   📋 Agregando Cliente General...")
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Verificar si la tabla tiene la columna fecha_creacion ahora
            cur.execute("PRAGMA table_info(clientes)")
            columnas_actuales = [col[1] for col in cur.fetchall()]
            
            if 'fecha_creacion' in columnas_actuales:
                cur.execute("""
                    INSERT INTO clientes (nombre, telefono, email, direccion, fecha_creacion)
                    VALUES ('Cliente General', '', '', '', ?)
                """, (fecha_actual,))
            else:
                cur.execute("""
                    INSERT INTO clientes (nombre, telefono, email, direccion)
                    VALUES ('Cliente General', '', '', '')
                """)
            print("   ✅ Cliente General agregado")
        else:
            print("   ✅ Cliente General ya existe")
        
        # === VERIFICAR TABLA CAJAS ===
        print("\n💰 Verificando tabla cajas...")
        cur.execute("PRAGMA table_info(cajas)")
        columnas_cajas = cur.fetchall()
        
        if not columnas_cajas:
            print("❌ Tabla cajas no existe, creándola...")
            cur.execute("""
                CREATE TABLE cajas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    descripcion TEXT,
                    creado_por INTEGER,
                    fecha_creacion TEXT DEFAULT '2025-01-01 00:00:00',
                    FOREIGN KEY (creado_por) REFERENCES usuarios(id)
                )
            """)
            print("✅ Tabla cajas creada")
        else:
            print("✅ Tabla cajas existe")
        
        # === VERIFICAR TABLA SESIONES_CAJA ===
        print("\n🔐 Verificando tabla sesiones_caja...")
        cur.execute("PRAGMA table_info(sesiones_caja)")
        columnas_sesiones = cur.fetchall()
        
        if not columnas_sesiones:
            print("❌ Tabla sesiones_caja no existe, creándola...")
            cur.execute("""
                CREATE TABLE sesiones_caja (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caja_id INTEGER NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    monto_apertura REAL DEFAULT 0,
                    monto_cierre REAL DEFAULT 0,
                    total_ventas REAL DEFAULT 0,
                    diferencia REAL DEFAULT 0,
                    estado TEXT DEFAULT 'Abierta',
                    fecha_apertura TEXT DEFAULT '2025-01-01 00:00:00',
                    fecha_cierre TEXT,
                    observaciones TEXT,
                    FOREIGN KEY (caja_id) REFERENCES cajas(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            """)
            print("✅ Tabla sesiones_caja creada")
        else:
            print("✅ Tabla sesiones_caja existe")
        
        # === VERIFICAR TABLA VENTAS ===
        print("\n🛒 Verificando tabla ventas...")
        cur.execute("PRAGMA table_info(ventas)")
        columnas_ventas = cur.fetchall()
        
        if not columnas_ventas:
            print("❌ Tabla ventas no existe, creándola...")
            cur.execute("""
                CREATE TABLE ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_venta TEXT UNIQUE,
                    sesion_caja_id INTEGER,
                    cliente_id INTEGER,
                    usuario_id INTEGER NOT NULL,
                    total REAL NOT NULL,
                    subtotal REAL DEFAULT 0,
                    descuento REAL DEFAULT 0,
                    monto_pagado REAL DEFAULT 0,
                    vuelto REAL DEFAULT 0,
                    metodo_pago TEXT DEFAULT 'Efectivo',
                    fecha_venta TEXT DEFAULT '2025-01-01 00:00:00',
                    estado TEXT DEFAULT 'Completada',
                    observaciones TEXT,
                    FOREIGN KEY (sesion_caja_id) REFERENCES sesiones_caja(id),
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            """)
            print("✅ Tabla ventas creada")
        else:
            print("✅ Tabla ventas existe")
        
        # === VERIFICAR TABLA DETALLE_VENTAS ===
        print("\n📋 Verificando tabla detalle_ventas...")
        cur.execute("PRAGMA table_info(detalle_ventas)")
        columnas_detalle = cur.fetchall()
        
        if not columnas_detalle:
            print("❌ Tabla detalle_ventas no existe, creándola...")
            cur.execute("""
                CREATE TABLE detalle_ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            """)
            print("✅ Tabla detalle_ventas creada")
        else:
            print("✅ Tabla detalle_ventas existe")
        
        # === CREAR ÍNDICES PARA RENDIMIENTO ===
        print("\n🔍 Creando índices...")
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)",
            "CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_usuario ON ventas(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_numero ON ventas(numero_venta)",
            "CREATE INDEX IF NOT EXISTS idx_sesiones_usuario ON sesiones_caja(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_sesiones_estado ON sesiones_caja(estado)",
            "CREATE INDEX IF NOT EXISTS idx_detalle_venta ON detalle_ventas(venta_id)",
            "CREATE INDEX IF NOT EXISTS idx_detalle_producto ON detalle_ventas(producto_id)",
            "CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre)",
        ]
        
        for indice in indices:
            try:
                cur.execute(indice)
            except Exception as e:
                print(f"   ⚠️ Índice ya existe o error: {e}")
        print("✅ Índices procesados")
        
        # === NORMALIZAR DATOS EXISTENTES ===
        print("\n🔧 Normalizando datos existentes...")
        
        # Actualizar productos sin stock
        cur.execute("UPDATE productos SET stock = 0 WHERE stock IS NULL")
        affected = cur.rowcount
        if affected > 0:
            print(f"   ✅ {affected} productos actualizados con stock = 0")
        
        # Actualizar productos sin unidad_medida
        cur.execute("UPDATE productos SET unidad_medida = COALESCE(unidad, 'Unitario') WHERE unidad_medida IS NULL OR unidad_medida = ''")
        affected = cur.rowcount
        if affected > 0:
            print(f"   ✅ {affected} productos actualizados con unidad_medida")
        
        # === VERIFICAR DATOS DE USUARIOS ===
        print("\n👤 Verificando usuarios...")
        cur.execute("SELECT COUNT(*) FROM usuarios")
        count_usuarios = cur.fetchone()[0]
        print(f"   📊 Usuarios en sistema: {count_usuarios}")
        
        # === DATOS DE PRUEBA BÁSICOS ===
        print("\n🌱 Verificando productos...")
        cur.execute("SELECT COUNT(*) FROM productos")
        count_productos = cur.fetchone()[0]
        print(f"   📊 Productos en sistema: {count_productos}")
        
        if count_productos < 3:  # Si hay muy pocos productos
            print("   📦 Insertando productos básicos...")
            productos_basicos = [
                ("Rosa", "Ornamentales", "Unitario", 15000, 25000, 10),
                ("Eucalipto", "Ornamentales", "Unitario", 12000, 20000, 5),
                ("Limón", "Cítricos", "Unitario", 18000, 30000, 8),
            ]
            
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for producto in productos_basicos:
                try:
                    # Verificar si ya existe
                    cur.execute("SELECT id FROM productos WHERE nombre = ?", (producto[0],))
                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO productos (nombre, categoria, unidad_medida, precio_compra, precio_venta, stock, fecha_creacion, fecha_actualizacion)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (*producto, fecha_actual, fecha_actual))
                        print(f"   ✅ Producto '{producto[0]}' agregado")
                except sqlite3.IntegrityError as e:
                    print(f"   ⚠️ Producto '{producto[0]}' ya existe o error: {e}")
        
        # === VERIFICAR INTEGRIDAD ===
        print("\n🔍 Verificando integridad...")
        cur.execute("PRAGMA foreign_key_check")
        errores_fk = cur.fetchall()
        if errores_fk:
            print(f"   ⚠️ {len(errores_fk)} errores de integridad encontrados")
            for error in errores_fk:
                print(f"     - {error}")
        else:
            print("   ✅ Integridad de datos correcta")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Base de datos actualizada exitosamente!")
        print(f"📂 Ubicación: {os.path.abspath(DB)}")
        print(f"⏰ Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando base de datos: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def mostrar_resumen_final():
    """Muestra un resumen final de la base de datos"""
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        print(f"\n📊 RESUMEN FINAL DE LA BASE DE DATOS")
        print("=" * 50)
        
        tablas = ["usuarios", "productos", "clientes", "cajas", "sesiones_caja", "ventas", "detalle_ventas"]
        
        for tabla in tablas:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {tabla}")
                count = cur.fetchone()[0]
                print(f"📋 {tabla:20} {count:>5} registros")
            except:
                print(f"❌ {tabla:20} No existe")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error mostrando resumen: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO ACTUALIZACIÓN DE BASE DE DATOS")
    print("=" * 50)
    
    # Ejecutar actualización
    if verificar_y_actualizar_bd():
        mostrar_resumen_final()
        print("\n✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("🎯 El sistema está listo para usar")
        print("🚀 Puede ejecutar: python main.py")
    else:
        print("\n❌ PROCESO FALLÓ")
        print("🔧 Revise los errores arriba")