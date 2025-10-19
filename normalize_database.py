import sqlite3
import os
from datetime import datetime

DB = "data/vivero.db"

def normalizar_base_datos():
    """Normaliza y corrige la estructura de la base de datos existente"""
    print("🔧 NORMALIZANDO BASE DE DATOS EXISTENTE")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        # === 1. VERIFICAR TABLA detalle_ventas vs detalle_venta ===
        print("\n📋 Verificando tablas de detalle de ventas...")
        
        # Verificar si existe detalle_venta (tabla antigua)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detalle_venta'")
        detalle_venta_existe = cur.fetchone()
        
        # Verificar si existe detalle_ventas (tabla correcta)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detalle_ventas'")
        detalle_ventas_existe = cur.fetchone()
        
        if detalle_venta_existe and detalle_ventas_existe:
            print("  ⚠️ Ambas tablas existen, migrar datos de detalle_venta a detalle_ventas...")
            
            # Verificar estructura de detalle_venta
            cur.execute("PRAGMA table_info(detalle_venta)")
            cols_detalle_venta = [col[1] for col in cur.fetchall()]
            
            # Verificar estructura de detalle_ventas
            cur.execute("PRAGMA table_info(detalle_ventas)")
            cols_detalle_ventas = [col[1] for col in cur.fetchall()]
            
            print(f"   📊 detalle_venta tiene: {cols_detalle_venta}")
            print(f"   📊 detalle_ventas tiene: {cols_detalle_ventas}")
            
            # Migrar datos si detalle_venta tiene datos
            cur.execute("SELECT COUNT(*) FROM detalle_venta")
            count_vieja = cur.fetchone()[0]
            
            if count_vieja > 0:
                print(f"   📦 Migrando {count_vieja} registros...")
                
                # Verificar si detalle_ventas tiene columna subtotal
                if 'subtotal' in cols_detalle_ventas and 'subtotal' not in cols_detalle_venta:
                    # Migrar calculando subtotal
                    cur.execute("""
                        INSERT OR IGNORE INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                        SELECT venta_id, producto_id, cantidad, precio_unitario, 
                               (cantidad * precio_unitario) as subtotal
                        FROM detalle_venta
                    """)
                else:
                    # Migrar con las columnas disponibles
                    cur.execute("""
                        INSERT OR IGNORE INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario)
                        SELECT venta_id, producto_id, cantidad, precio_unitario
                        FROM detalle_venta
                    """)
                
                migrados = cur.rowcount
                print(f"   ✅ {migrados} registros migrados")
                
                # Eliminar tabla antigua después de migrar
                cur.execute("DROP TABLE detalle_venta")
                print("   🗑️ Tabla detalle_venta eliminada")
        
        elif detalle_venta_existe and not detalle_ventas_existe:
            print("   📋 Renombrando detalle_venta a detalle_ventas...")
            cur.execute("ALTER TABLE detalle_venta RENAME TO detalle_ventas")
            
            # Agregar columna subtotal si no existe
            cur.execute("PRAGMA table_info(detalle_ventas)")
            cols = [col[1] for col in cur.fetchall()]
            
            if 'subtotal' not in cols:
                print("   📋 Agregando columna subtotal...")
                cur.execute("ALTER TABLE detalle_ventas ADD COLUMN subtotal DECIMAL(15,0)")
                cur.execute("UPDATE detalle_ventas SET subtotal = cantidad * precio_unitario WHERE subtotal IS NULL")
                print("   ✅ Columna subtotal agregada y calculada")
        
        # === 2. VERIFICAR Y CORREGIR TABLA PRODUCTOS ===
        print("\n📦 Normalizando tabla productos...")
        
        cur.execute("PRAGMA table_info(productos)")
        cols_productos = cur.fetchall()
        cols_nombres = [col[1] for col in cols_productos]
        
        print(f"   📊 Columnas actuales: {cols_nombres}")
        
        # Agregar columnas faltantes si es necesario
        columnas_requeridas = {
            'stock': ('INTEGER', 0),
            'unidad_medida': ('TEXT', 'Unitario'),
            'fecha_creacion': ('TEXT', '2025-01-01 00:00:00'),
            'fecha_actualizacion': ('TEXT', '2025-01-01 00:00:00')
        }
        
        for col_name, (col_type, default_val) in columnas_requeridas.items():
            if col_name not in cols_nombres:
                print(f"   📋 Agregando columna {col_name}...")
                cur.execute(f"ALTER TABLE productos ADD COLUMN {col_name} {col_type} DEFAULT ?", (default_val,))
                print(f"   ✅ Columna {col_name} agregada")
        
        # Normalizar datos de productos
        print("   🔧 Normalizando datos de productos...")
        
        # Actualizar unidad_medida desde unidad si está vacía
        cur.execute("""
            UPDATE productos 
            SET unidad_medida = COALESCE(unidad, 'Unitario') 
            WHERE unidad_medida IS NULL OR unidad_medida = ''
        """)
        
        # Actualizar stock NULL a 0
        cur.execute("UPDATE productos SET stock = 0 WHERE stock IS NULL")
        
        # Actualizar precios NULL a 0
        cur.execute("UPDATE productos SET precio_compra = 0 WHERE precio_compra IS NULL")
        cur.execute("UPDATE productos SET precio_venta = 0 WHERE precio_venta IS NULL")
        
        print("   ✅ Datos de productos normalizados")
        
        # === 3. VERIFICAR TABLA CLIENTES ===
        print("\n👥 Normalizando tabla clientes...")
        
        # Verificar si existe Cliente General
        cur.execute("SELECT id FROM clientes WHERE nombre = 'Cliente General'")
        if not cur.fetchone():
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute("""
                INSERT INTO clientes (nombre, telefono, email, direccion, fecha_creacion)
                VALUES ('Cliente General', '', '', '', ?)
            """, (fecha_actual,))
            print("   ✅ Cliente General agregado")
        else:
            print("   ✅ Cliente General ya existe")
        
        # === 4. CREAR ÍNDICES FALTANTES ===
        print("\n🔍 Creando índices para optimización...")
        
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_productos_nombre_busqueda ON productos(nombre)",
            "CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_fecha_busqueda ON ventas(fecha_venta)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id)",
            "CREATE INDEX IF NOT EXISTS idx_detalle_ventas_venta ON detalle_ventas(venta_id)",
            "CREATE INDEX IF NOT EXISTS idx_detalle_ventas_producto ON detalle_ventas(producto_id)",
            "CREATE INDEX IF NOT EXISTS idx_sesiones_usuario ON sesiones_caja(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre)",
        ]
        
        for idx in indices:
            try:
                cur.execute(idx)
            except Exception as e:
                print(f"   ⚠️ Índice ya existe o error: {e}")
        
        print("   ✅ Índices procesados")
        
        # === 5. LIMPIAR DATOS DUPLICADOS ===
        print("\n🧹 Limpiando datos duplicados...")
        
        # Eliminar productos duplicados por nombre (mantener el más reciente)
        cur.execute("""
            DELETE FROM productos 
            WHERE id NOT IN (
                SELECT MAX(id) 
                FROM productos 
                GROUP BY LOWER(TRIM(nombre))
            )
        """)
        duplicados_productos = cur.rowcount
        if duplicados_productos > 0:
            print(f"   🗑️ {duplicados_productos} productos duplicados eliminados")
        
        # === 6. VERIFICAR INTEGRIDAD REFERENCIAL ===
        print("\n🔍 Verificando integridad referencial...")
        
        # Verificar ventas sin cliente válido
        cur.execute("""
            SELECT COUNT(*) FROM ventas v 
            LEFT JOIN clientes c ON v.cliente_id = c.id 
            WHERE c.id IS NULL
        """)
        ventas_huerfanas = cur.fetchone()[0]
        
        if ventas_huerfanas > 0:
            print(f"   ⚠️ {ventas_huerfanas} ventas sin cliente válido")
            # Asignar al Cliente General
            cur.execute("SELECT id FROM clientes WHERE nombre = 'Cliente General'")
            cliente_general_id = cur.fetchone()[0]
            
            cur.execute("""
                UPDATE ventas 
                SET cliente_id = ? 
                WHERE cliente_id NOT IN (SELECT id FROM clientes)
            """, (cliente_general_id,))
            print(f"   ✅ Ventas asignadas al Cliente General")
        
        # Verificar detalles de ventas sin venta válida
        cur.execute("""
            SELECT COUNT(*) FROM detalle_ventas dv 
            LEFT JOIN ventas v ON dv.venta_id = v.id 
            WHERE v.id IS NULL
        """)
        detalles_huerfanos = cur.fetchone()[0]
        
        if detalles_huerfanos > 0:
            print(f"   🗑️ {detalles_huerfanos} detalles huérfanos eliminados")
            cur.execute("""
                DELETE FROM detalle_ventas 
                WHERE venta_id NOT IN (SELECT id FROM ventas)
            """)
        
        # === 7. ESTADÍSTICAS FINALES ===
        print("\n📊 ESTADÍSTICAS FINALES")
        print("-" * 30)
        
        tablas_importantes = [
            'usuarios', 'productos', 'clientes', 'ventas', 
            'detalle_ventas', 'cajas', 'sesiones_caja'
        ]
        
        for tabla in tablas_importantes:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {tabla}")
                count = cur.fetchone()[0]
                print(f"   📋 {tabla:15} {count:>5} registros")
            except:
                print(f"   ❌ {tabla:15} No existe")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ NORMALIZACIÓN COMPLETADA EXITOSAMENTE")
        print(f"⏰ Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error normalizando base de datos: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def hacer_backup():
    """Hacer backup antes de normalizar"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"data/vivero_backup_{timestamp}.db"
        
        import shutil
        shutil.copy2(DB, backup_file)
        print(f"💾 Backup creado: {backup_file}")
        return backup_file
        
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        return None

if __name__ == "__main__":
    print("🚀 INICIANDO NORMALIZACIÓN DE BASE DE DATOS")
    print("=" * 50)
    
    # Crear backup
    backup_file = hacer_backup()
    
    if backup_file:
        # Ejecutar normalización
        if normalizar_base_datos():
            print(f"\n🎉 PROCESO COMPLETADO EXITOSAMENTE")
            print(f"📂 Backup disponible en: {backup_file}")
            print(f"🚀 El sistema está listo para usar")
        else:
            print(f"\n❌ PROCESO FALLÓ")
            print(f"🔄 Puedes restaurar desde: {backup_file}")
    else:
        print("❌ No se pudo crear backup, proceso cancelado")