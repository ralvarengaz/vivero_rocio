import sqlite3

DB = "data/vivero.db"

def normalizar_tabla_clientes():
    """Normaliza la tabla clientes para que sea compatible"""
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        print("🔧 NORMALIZANDO TABLA CLIENTES")
        print("=" * 35)
        
        # Verificar estructura actual
        cur.execute("PRAGMA table_info(clientes)")
        columnas = cur.fetchall()
        columnas_existentes = [col[1] for col in columnas]
        
        print(f"📋 Columnas actuales: {columnas_existentes}")
        
        cambios_realizados = []
        
        # Agregar columnas faltantes si es necesario
        if 'ruc' not in columnas_existentes and 'ruc_ci' in columnas_existentes:
            print("🔄 Renombrando ruc_ci a ruc...")
            # SQLite no permite renombrar columnas directamente, así que agregamos una nueva
            cur.execute("ALTER TABLE clientes ADD COLUMN ruc TEXT")
            cur.execute("UPDATE clientes SET ruc = ruc_ci WHERE ruc_ci IS NOT NULL")
            cambios_realizados.append("Columna ruc agregada desde ruc_ci")
        
        if 'telefono' not in columnas_existentes and 'tel' in columnas_existentes:
            print("🔄 Renombrando tel a telefono...")
            cur.execute("ALTER TABLE clientes ADD COLUMN telefono TEXT")
            cur.execute("UPDATE telefono SET telefono = tel WHERE tel IS NOT NULL")
            cambios_realizados.append("Columna telefono agregada desde tel")
        
        # Verificar que existan las columnas básicas
        columnas_requeridas = ['nombre', 'ruc', 'telefono', 'ciudad', 'ubicacion', 'correo']
        
        for col in columnas_requeridas:
            if col not in columnas_existentes:
                print(f"➕ Agregando columna {col}...")
                cur.execute(f"ALTER TABLE clientes ADD COLUMN {col} TEXT")
                cambios_realizados.append(f"Columna {col} agregada")
        
        # Limpiar datos nulos
        print("🧹 Limpiando datos nulos...")
        cur.execute("UPDATE clientes SET ruc = '' WHERE ruc IS NULL")
        cur.execute("UPDATE clientes SET telefono = '' WHERE telefono IS NULL")
        cur.execute("UPDATE clientes SET ciudad = '' WHERE ciudad IS NULL")
        cur.execute("UPDATE clientes SET ubicacion = '' WHERE ubicacion IS NULL")
        cur.execute("UPDATE clientes SET correo = '' WHERE correo IS NULL")
        
        conn.commit()
        
        # Verificar resultado
        cur.execute("PRAGMA table_info(clientes)")
        columnas_finales = cur.fetchall()
        
        print(f"\n✅ RESULTADO FINAL")
        print(f"📊 Columnas finales:")
        for col in columnas_finales:
            print(f"  - {col[1]:15} {col[2]:10}")
        
        if cambios_realizados:
            print(f"\n🔧 Cambios realizados:")
            for cambio in cambios_realizados:
                print(f"  ✅ {cambio}")
        else:
            print(f"\n💡 No se necesitaron cambios")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error normalizando tabla: {e}")
        return False

if __name__ == "__main__":
    normalizar_tabla_clientes()