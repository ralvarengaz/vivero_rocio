import sqlite3
import os

DB = "data/vivero.db"

def corregir_problema_unidad():
    """Corrige el problema de la columna unidad NOT NULL"""
    print("🔧 CORRIGIENDO PROBLEMA DE COLUMNA 'unidad'")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        # === 1. VERIFICAR ESTRUCTURA DE LA TABLA ===
        print("\n📋 Verificando estructura de tabla productos...")
        cur.execute("PRAGMA table_info(productos)")
        columnas = cur.fetchall()
        
        print("   Columnas actuales:")
        for col in columnas:
            null_info = "NOT NULL" if col[3] else "NULL"
            default_info = f"DEFAULT {col[4]}" if col[4] else "Sin DEFAULT"
            print(f"     - {col[1]:20} {col[2]:10} {null_info:8} {default_info}")
        
        # === 2. VERIFICAR DATOS CON PROBLEMAS ===
        print("\n🔍 Verificando datos problemáticos...")
        
        # Verificar registros con unidad NULL
        cur.execute("SELECT id, nombre, unidad, unidad_medida FROM productos WHERE unidad IS NULL")
        unidad_null = cur.fetchall()
        
        if unidad_null:
            print(f"   ❌ {len(unidad_null)} productos con unidad NULL:")
            for prod in unidad_null:
                print(f"     ID: {prod[0]}, Nombre: '{prod[1]}', unidad: {prod[2]}, unidad_medida: {prod[3]}")
        else:
            print("   ✅ No hay productos con unidad NULL")
        
        # === 3. CORREGIR DATOS ===
        print("\n🔧 Corrigiendo datos...")
        
        # Actualizar unidad NULL usando unidad_medida o 'Unitario'
        cur.execute("""
            UPDATE productos 
            SET unidad = COALESCE(unidad_medida, 'Unitario') 
            WHERE unidad IS NULL
        """)
        actualizados = cur.rowcount
        if actualizados > 0:
            print(f"   ✅ {actualizados} productos actualizados con unidad")
        
        # Actualizar unidad_medida NULL usando unidad o 'Unitario'
        cur.execute("""
            UPDATE productos 
            SET unidad_medida = COALESCE(unidad, 'Unitario') 
            WHERE unidad_medida IS NULL
        """)
        actualizados_medida = cur.rowcount
        if actualizados_medida > 0:
            print(f"   ✅ {actualizados_medida} productos actualizados con unidad_medida")
        
        # === 4. VERIFICAR OTRAS COLUMNAS PROBLEMÁTICAS ===
        print("\n🔍 Verificando otras columnas...")
        
        # Verificar otras columnas NOT NULL
        columnas_not_null = [col[1] for col in columnas if col[3] == 1]  # NOT NULL = 1
        print(f"   📊 Columnas NOT NULL: {columnas_not_null}")
        
        for col_name in columnas_not_null:
            if col_name != 'id':  # Skip primary key
                cur.execute(f"SELECT COUNT(*) FROM productos WHERE {col_name} IS NULL")
                null_count = cur.fetchone()[0]
                if null_count > 0:
                    print(f"   ❌ {null_count} registros con {col_name} NULL")
                    
                    # Corregir según el tipo de columna
                    if col_name in ['nombre', 'categoria', 'unidad', 'unidad_medida']:
                        default_val = 'Sin especificar' if col_name in ['nombre', 'categoria'] else 'Unitario'
                        cur.execute(f"UPDATE productos SET {col_name} = ? WHERE {col_name} IS NULL", (default_val,))
                        print(f"   ✅ {col_name} corregido con '{default_val}'")
                    elif col_name in ['precio_compra', 'precio_venta', 'stock']:
                        cur.execute(f"UPDATE productos SET {col_name} = 0 WHERE {col_name} IS NULL")
                        print(f"   ✅ {col_name} corregido con 0")
        
        # === 5. PROBAR INSERCIÓN DE FRUTILLA ===
        print("\n🧪 Probando inserción de Frutilla...")
        
        # Verificar si ya existe
        cur.execute("SELECT id FROM productos WHERE LOWER(TRIM(nombre)) = 'frutilla'")
        existe = cur.fetchone()
        
        if existe:
            print(f"   ⚠️ Frutilla ya existe con ID: {existe[0]}")
        else:
            try:
                # Probar inserción con todos los campos obligatorios
                cur.execute("""
                    INSERT INTO productos (
                        nombre, categoria, unidad, precio_compra, precio_venta, 
                        unidad_medida, stock
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ('Frutilla', 'Frutales', 'Unitario', 5000, 10000, 'Unitario', 10))
                
                nuevo_id = cur.lastrowid
                print(f"   ✅ Frutilla insertada exitosamente con ID: {nuevo_id}")
                
            except Exception as e:
                print(f"   ❌ Error insertando Frutilla: {e}")
                
                # Mostrar qué columnas están causando problemas
                cur.execute("PRAGMA table_info(productos)")
                cols_info = cur.fetchall()
                not_null_cols = [col[1] for col in cols_info if col[3] == 1 and col[1] != 'id']
                print(f"   📋 Columnas NOT NULL requeridas: {not_null_cols}")
        
        conn.commit()
        
        # === 6. VERIFICACIÓN FINAL ===
        print(f"\n📊 VERIFICACIÓN FINAL")
        print("-" * 25)
        
        cur.execute("SELECT COUNT(*) FROM productos")
        total = cur.fetchone()[0]
        print(f"   📦 Total de productos: {total}")
        
        # Verificar que no hay más NULL en columnas NOT NULL
        problemas_restantes = 0
        for col_name in columnas_not_null:
            if col_name != 'id':
                cur.execute(f"SELECT COUNT(*) FROM productos WHERE {col_name} IS NULL")
                null_count = cur.fetchone()[0]
                if null_count > 0:
                    print(f"   ❌ {null_count} registros aún tienen {col_name} NULL")
                    problemas_restantes += null_count
        
        if problemas_restantes == 0:
            print("   ✅ Todos los campos NOT NULL están correctos")
        
        conn.close()
        
        print(f"\n✅ CORRECCIÓN COMPLETADA")
        return True
        
    except Exception as e:
        print(f"❌ Error corrigiendo: {e}")
        import traceback
        traceback.print_exc()
        return False

def mostrar_esquema_productos():
    """Muestra el esquema completo de la tabla productos"""
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        print(f"\n📋 ESQUEMA COMPLETO DE TABLA PRODUCTOS")
        print("=" * 50)
        
        # Obtener el SQL de creación de la tabla
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='productos'")
        schema = cur.fetchone()
        
        if schema:
            print("   SQL de creación:")
            print(f"   {schema[0]}")
        
        print(f"\n📊 INFORMACIÓN DETALLADA DE COLUMNAS")
        print("-" * 40)
        
        cur.execute("PRAGMA table_info(productos)")
        columnas = cur.fetchall()
        
        for col in columnas:
            print(f"   Columna: {col[1]}")
            print(f"     Tipo: {col[2]}")
            print(f"     NOT NULL: {'Sí' if col[3] else 'No'}")
            print(f"     DEFAULT: {col[4] if col[4] else 'Ninguno'}")
            print(f"     PRIMARY KEY: {'Sí' if col[5] else 'No'}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error mostrando esquema: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO CORRECCIÓN DE PROBLEMA DE UNIDAD")
    print("=" * 50)
    
    # Mostrar esquema actual
    mostrar_esquema_productos()
    
    # Ejecutar corrección
    if corregir_problema_unidad():
        print(f"\n🎉 PROCESO COMPLETADO")
        print(f"🚀 Ahora puede intentar agregar productos nuevamente")
        print(f"\n💡 RECOMENDACIÓN:")
        print(f"   Reinicie la aplicación: python main.py")
    else:
        print(f"\n❌ PROCESO FALLÓ")