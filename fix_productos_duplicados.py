import sqlite3
import os

DB = "data/vivero.db"

def diagnosticar_y_corregir():
    """Diagnostica y corrige problemas de productos duplicados"""
    print("🔍 DIAGNOSTICANDO PROBLEMA DE PRODUCTOS DUPLICADOS")
    print("=" * 55)
    
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        # === 1. BUSCAR EL PRODUCTO "FRUTILLA" ===
        print("\n🔍 Buscando producto 'Frutilla'...")
        
        # Búsqueda exacta
        cur.execute("SELECT * FROM productos WHERE nombre = 'Frutilla'")
        exacto = cur.fetchall()
        
        # Búsqueda case-insensitive
        cur.execute("SELECT * FROM productos WHERE LOWER(nombre) = 'frutilla'")
        case_insensitive = cur.fetchall()
        
        # Búsqueda con LIKE para variaciones
        cur.execute("SELECT * FROM productos WHERE nombre LIKE '%frutilla%' OR nombre LIKE '%Frutilla%'")
        variaciones = cur.fetchall()
        
        print(f"   📊 Coincidencias exactas: {len(exacto)}")
        print(f"   📊 Coincidencias case-insensitive: {len(case_insensitive)}")
        print(f"   📊 Variaciones encontradas: {len(variaciones)}")
        
        if exacto:
            print("   ❌ Producto 'Frutilla' ya existe:")
            for prod in exacto:
                print(f"     ID: {prod[0]}, Nombre: '{prod[1]}', Categoría: {prod[2]}")
        
        if variaciones:
            print("   📋 Todas las variaciones encontradas:")
            for prod in variaciones:
                print(f"     ID: {prod[0]}, Nombre: '{prod[1]}', Categoría: {prod[2]}")
        
        # === 2. VERIFICAR ESTRUCTURA DEL ÍNDICE ===
        print("\n🔍 Verificando índices...")
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='productos'")
        indices = cur.fetchall()
        
        print("   📊 Índices existentes:")
        for idx in indices:
            print(f"     - {idx[0]}")
        
        # === 3. BUSCAR DUPLICADOS GENERALES ===
        print("\n🔍 Buscando todos los duplicados...")
        cur.execute("""
            SELECT LOWER(TRIM(nombre)) as nombre_norm, COUNT(*) as cantidad, 
                   GROUP_CONCAT(id) as ids,
                   GROUP_CONCAT(nombre) as nombres_originales
            FROM productos 
            GROUP BY LOWER(TRIM(nombre)) 
            HAVING COUNT(*) > 1
        """)
        duplicados = cur.fetchall()
        
        if duplicados:
            print(f"   ❌ Se encontraron {len(duplicados)} grupos de duplicados:")
            for dup in duplicados:
                print(f"     - '{dup[0]}': {dup[1]} repeticiones (IDs: {dup[2]})")
                print(f"       Nombres originales: {dup[3]}")
        else:
            print("   ✅ No se encontraron duplicados obvios")
        
        # === 4. VERIFICAR ESPACIOS EN BLANCO ===
        print("\n🔍 Verificando espacios en blanco...")
        cur.execute("""
            SELECT id, nombre, LENGTH(nombre) as longitud,
                   CASE WHEN nombre != TRIM(nombre) THEN 'Tiene espacios' ELSE 'Sin espacios' END as espacios
            FROM productos 
            WHERE nombre LIKE '%frutilla%' OR nombre LIKE '%Frutilla%'
        """)
        espacios = cur.fetchall()
        
        if espacios:
            print("   📊 Productos con posibles espacios:")
            for esp in espacios:
                print(f"     ID: {esp[0]}, Nombre: '{esp[1]}', Longitud: {esp[2]}, Estado: {esp[3]}")
        
        # === 5. OPCIÓN DE CORRECCIÓN ===
        print(f"\n🔧 OPCIONES DE CORRECCIÓN")
        print("-" * 30)
        
        if duplicados or (case_insensitive and input("\n¿Desea proceder con la corrección automática? (s/n): ").lower() == 's'):
            
            # Limpiar espacios en nombres
            print("\n🧹 Limpiando espacios en nombres...")
            cur.execute("UPDATE productos SET nombre = TRIM(nombre) WHERE nombre != TRIM(nombre)")
            espacios_limpiados = cur.rowcount
            if espacios_limpiados > 0:
                print(f"   ✅ {espacios_limpiados} nombres limpiados")
            
            # Eliminar duplicados (mantener el más reciente)
            if duplicados:
                print("\n🗑️ Eliminando duplicados...")
                for dup in duplicados:
                    ids = dup[2].split(',')
                    ids_a_eliminar = ids[:-1]  # Mantener el último (más reciente)
                    
                    for id_eliminar in ids_a_eliminar:
                        cur.execute("DELETE FROM productos WHERE id = ?", (int(id_eliminar),))
                        print(f"     🗑️ Producto ID {id_eliminar} eliminado")
            
            # Recrear índice único
            print("\n🔧 Recreando índice único...")
            try:
                cur.execute("DROP INDEX IF EXISTS idx_productos_nombre_nocase")
                cur.execute("""
                    CREATE UNIQUE INDEX idx_productos_nombre_nocase 
                    ON productos (nombre COLLATE NOCASE)
                """)
                print("   ✅ Índice único recreado")
            except Exception as e:
                print(f"   ❌ Error recreando índice: {e}")
            
            conn.commit()
            print("\n✅ Correcciones aplicadas")
            
        # === 6. VERIFICACIÓN FINAL ===
        print(f"\n📊 VERIFICACIÓN FINAL")
        print("-" * 25)
        
        # Contar productos totales
        cur.execute("SELECT COUNT(*) FROM productos")
        total = cur.fetchone()[0]
        print(f"   📦 Total de productos: {total}")
        
        # Verificar si ahora se puede insertar Frutilla
        try:
            cur.execute("SELECT 1 FROM productos WHERE LOWER(nombre) = 'frutilla' LIMIT 1")
            existe = cur.fetchone()
            
            if existe:
                print("   ❌ 'Frutilla' aún existe en la base de datos")
                print("   💡 Sugerencia: Use un nombre ligeramente diferente como 'Frutilla Nueva'")
            else:
                print("   ✅ 'Frutilla' no existe, se puede insertar")
                
                # Probar inserción
                if input("\n¿Desea probar insertar 'Frutilla' ahora? (s/n): ").lower() == 's':
                    cur.execute("""
                        INSERT INTO productos (nombre, categoria, unidad_medida, precio_compra, precio_venta, stock)
                        VALUES ('Frutilla', 'Frutales', 'Unitario', 5000, 10000, 10)
                    """)
                    conn.commit()
                    print("   ✅ Producto 'Frutilla' insertado exitosamente")
        
        except Exception as e:
            print(f"   ❌ Error en verificación final: {e}")
        
        conn.close()
        
        print(f"\n🎉 DIAGNÓSTICO COMPLETADO")
        return True
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return False

def mostrar_todos_productos():
    """Muestra todos los productos para verificación"""
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        print(f"\n📋 LISTA COMPLETA DE PRODUCTOS")
        print("-" * 40)
        
        cur.execute("SELECT id, nombre, categoria, stock FROM productos ORDER BY id")
        productos = cur.fetchall()
        
        for prod in productos:
            print(f"   {prod[0]:3} | {prod[1]:20} | {prod[2]:15} | Stock: {prod[3]}")
        
        print(f"\n📊 Total: {len(productos)} productos")
        conn.close()
        
    except Exception as e:
        print(f"❌ Error mostrando productos: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO DIAGNÓSTICO DE PRODUCTOS")
    print("=" * 45)
    
    # Mostrar productos actuales
    mostrar_todos_productos()
    
    # Ejecutar diagnóstico
    if diagnosticar_y_corregir():
        print(f"\n✅ PROCESO COMPLETADO")
        print(f"🚀 Intente agregar el producto nuevamente")
    else:
        print(f"\n❌ PROCESO FALLÓ")