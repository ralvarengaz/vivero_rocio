import sqlite3
from datetime import datetime

DB = "data/vivero.db"

def crear_tablas_ventas():
    """Crea y actualiza las tablas necesarias para el sistema de ventas PdV"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    print("🗃️ Configurando tablas del sistema de ventas...")
    
    # ===== TABLA PRODUCTOS - Verificar y actualizar estructura =====
    try:
        # Obtener estructura actual de productos
        cur.execute("PRAGMA table_info(productos)")
        columnas_productos = [col[1] for col in cur.fetchall()]
        print(f"📋 Columnas actuales en productos: {columnas_productos}")
        
        # Agregar columnas faltantes si no existen
        if 'precio' not in columnas_productos:
            print("➕ Agregando columna 'precio' a productos...")
            cur.execute("ALTER TABLE productos ADD COLUMN precio DECIMAL(15,0) DEFAULT 0")
        
        if 'stock' not in columnas_productos:
            print("➕ Agregando columna 'stock' a productos...")
            cur.execute("ALTER TABLE productos ADD COLUMN stock INTEGER DEFAULT 0")
        
        if 'unidad_medida' not in columnas_productos:
            print("➕ Agregando columna 'unidad_medida' a productos...")
            cur.execute("ALTER TABLE productos ADD COLUMN unidad_medida TEXT DEFAULT 'Unidad'")
            
    except Exception as e:
        print(f"⚠️ Error actualizando productos: {e}")
    
    # ===== TABLA VENTAS - Verificar y actualizar estructura =====
    try:
        # Verificar si existe la tabla ventas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ventas'")
        if not cur.fetchone():
            print("📦 Creando tabla ventas...")
            cur.execute("""
                CREATE TABLE ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_venta TEXT UNIQUE NOT NULL,
                    sesion_caja_id INTEGER,
                    cliente_id INTEGER NULL,
                    usuario_id INTEGER NOT NULL,
                    subtotal DECIMAL(15,0) NOT NULL,
                    descuento DECIMAL(15,0) DEFAULT 0,
                    total DECIMAL(15,0) NOT NULL,
                    monto_pagado DECIMAL(15,0) NOT NULL,
                    vuelto DECIMAL(15,0) DEFAULT 0,
                    metodo_pago TEXT DEFAULT 'Efectivo',
                    estado TEXT DEFAULT 'Completada',
                    fecha_venta DATETIME DEFAULT CURRENT_TIMESTAMP,
                    observaciones TEXT,
                    FOREIGN KEY (sesion_caja_id) REFERENCES sesiones_caja(id),
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            """)
        else:
            # Verificar columnas de ventas
            cur.execute("PRAGMA table_info(ventas)")
            columnas_ventas = [col[1] for col in cur.fetchall()]
            print(f"📋 Columnas actuales en ventas: {columnas_ventas}")
            
            # Agregar columnas faltantes
            columnas_requeridas = [
                ('sesion_caja_id', 'INTEGER'),
                ('subtotal', 'DECIMAL(15,0) DEFAULT 0'),
                ('descuento', 'DECIMAL(15,0) DEFAULT 0'),
                ('monto_pagado', 'DECIMAL(15,0) DEFAULT 0'),
                ('vuelto', 'DECIMAL(15,0) DEFAULT 0'),
                ('metodo_pago', 'TEXT DEFAULT "Efectivo"'),
                ('numero_venta', 'TEXT'),
            ]
            
            for columna, tipo in columnas_requeridas:
                if columna not in columnas_ventas:
                    print(f"➕ Agregando columna '{columna}' a ventas...")
                    cur.execute(f"ALTER TABLE ventas ADD COLUMN {columna} {tipo}")
                    
    except Exception as e:
        print(f"⚠️ Error actualizando ventas: {e}")
    
    # ===== TABLA CAJAS =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cajas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            estado TEXT DEFAULT 'Cerrada',
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            creado_por INTEGER,
            FOREIGN KEY (creado_por) REFERENCES usuarios(id)
        )
    """)
    
    # ===== TABLA SESIONES_CAJA =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sesiones_caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caja_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_cierre DATETIME NULL,
            monto_apertura DECIMAL(15,0) DEFAULT 0,
            monto_cierre DECIMAL(15,0) DEFAULT 0,
            total_ventas DECIMAL(15,0) DEFAULT 0,
            total_efectivo DECIMAL(15,0) DEFAULT 0,
            diferencia DECIMAL(15,0) DEFAULT 0,
            estado TEXT DEFAULT 'Abierta',
            observaciones TEXT,
            FOREIGN KEY (caja_id) REFERENCES cajas(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    
    # ===== TABLA DETALLE_VENTAS =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario DECIMAL(15,0) NOT NULL,
            subtotal DECIMAL(15,0) NOT NULL,
            FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)
    
    # ===== INSERTAR CAJA POR DEFECTO =====
    cur.execute("SELECT COUNT(*) FROM cajas")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO cajas (nombre, descripcion, creado_por)
            VALUES ('Caja Principal', 'Caja principal del vivero', 1)
        """)
        print("✅ Caja principal creada")
    
    # ===== ACTUALIZAR PRODUCTOS EXISTENTES CON PRECIOS =====
    try:
        # Verificar si hay productos sin precio
        cur.execute("SELECT COUNT(*) FROM productos WHERE precio IS NULL OR precio = 0")
        productos_sin_precio = cur.fetchone()[0]
        
        if productos_sin_precio > 0:
            print(f"🔄 Actualizando {productos_sin_precio} productos con precios por defecto...")
            
            # Actualizar productos existentes con precios y stock por defecto
            productos_precios = [
                ('Rosa Roja', 25000, 50, 'Unidad'),
                ('Fertilizante Orgánico', 45000, 30, 'Bolsa'),
                ('Maceta Barro', 15000, 100, 'Unidad'),
                ('Semillas Tomate', 8000, 200, 'Sobre'),
                ('Planta Pothos', 35000, 20, 'Unidad'),
                ('Sustrato Universal', 28000, 40, 'Bolsa'),
                ('Regadera Plástica', 18000, 25, 'Unidad'),
                ('Abono Líquido', 22000, 60, 'Botella'),
            ]
            
            for nombre, precio, stock, unidad in productos_precios:
                cur.execute("""
                    UPDATE productos 
                    SET precio = ?, stock = ?, unidad_medida = ? 
                    WHERE nombre LIKE ? AND (precio IS NULL OR precio = 0)
                """, (precio, stock, unidad, f'%{nombre}%'))
            
            # Para productos que no coincidan, poner valores por defecto
            cur.execute("""
                UPDATE productos 
                SET precio = 10000, stock = 10, unidad_medida = 'Unidad'
                WHERE precio IS NULL OR precio = 0
            """)
        
    except Exception as e:
        print(f"⚠️ Error actualizando precios: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Tablas del sistema de ventas configuradas correctamente")

def insertar_productos_ejemplo():
    """Inserta productos de ejemplo si no existen"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    try:
        # Verificar si hay productos
        cur.execute("SELECT COUNT(*) FROM productos")
        if cur.fetchone()[0] == 0:
            print("📦 Insertando productos de ejemplo...")
            productos_ejemplo = [
                ('Rosa Roja', 'Flores', 25000, 50, 'Unidad', 'Rosa roja natural'),
                ('Fertilizante Orgánico', 'Fertilizantes', 45000, 30, 'Bolsa', 'Fertilizante orgánico 5kg'),
                ('Maceta Barro', 'Macetas', 15000, 100, 'Unidad', 'Maceta de barro mediana'),
                ('Semillas Tomate', 'Semillas', 8000, 200, 'Sobre', 'Semillas de tomate cherry'),
                ('Planta Pothos', 'Plantas', 35000, 20, 'Unidad', 'Planta pothos en maceta'),
                ('Sustrato Universal', 'Sustratos', 28000, 40, 'Bolsa', 'Sustrato universal 20kg'),
                ('Regadera Plástica', 'Herramientas', 18000, 25, 'Unidad', 'Regadera plástica 5L'),
                ('Abono Líquido', 'Fertilizantes', 22000, 60, 'Botella', 'Abono líquido 1L'),
                ('Pala de Jardín', 'Herramientas', 32000, 15, 'Unidad', 'Pala de jardín con mango de madera'),
                ('Tierra Negra', 'Sustratos', 12000, 80, 'Bolsa', 'Tierra negra 10kg'),
            ]
            
            for producto in productos_ejemplo:
                cur.execute("""
                    INSERT INTO productos (nombre, categoria, precio, stock, unidad_medida, descripcion, estado, creado_por)
                    VALUES (?, ?, ?, ?, ?, ?, 'Activo', 1)
                """, producto)
            
            print("✅ Productos de ejemplo insertados")
        else:
            print("ℹ️ Ya existen productos en la base de datos")
    
    except Exception as e:
        print(f"⚠️ Error insertando productos: {e}")
    
    conn.commit()
    conn.close()

def verificar_estructura_bd():
    """Verifica y muestra la estructura actual de la BD"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    print("\n🔍 === VERIFICACIÓN DE ESTRUCTURA DE BD ===")
    
    # Verificar tablas existentes
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = [tabla[0] for tabla in cur.fetchall()]
    print(f"📋 Tablas: {tablas}")
    
    # Verificar estructura de productos
    if 'productos' in tablas:
        cur.execute("PRAGMA table_info(productos)")
        cols_productos = cur.fetchall()
        print(f"🛍️ Productos - Columnas: {[col[1] for col in cols_productos]}")
        
        # Contar productos
        cur.execute("SELECT COUNT(*) FROM productos")
        count_productos = cur.fetchone()[0]
        print(f"📊 Total productos: {count_productos}")
    
    # Verificar estructura de ventas
    if 'ventas' in tablas:
        cur.execute("PRAGMA table_info(ventas)")
        cols_ventas = cur.fetchall()
        print(f"💰 Ventas - Columnas: {[col[1] for col in cols_ventas]}")
    
    # Verificar sesiones de caja
    if 'sesiones_caja' in tablas:
        cur.execute("SELECT COUNT(*) FROM sesiones_caja WHERE estado = 'Abierta'")
        sesiones_abiertas = cur.fetchone()[0]
        print(f"📦 Sesiones de caja abiertas: {sesiones_abiertas}")
    
    conn.close()
    print("✅ Verificación completada\n")

if __name__ == "__main__":
    print("🚀 Configurando sistema de ventas completo...")
    verificar_estructura_bd()
    crear_tablas_ventas()
    insertar_productos_ejemplo()
    verificar_estructura_bd()
    print("🎉 Configuración completada exitosamente!")