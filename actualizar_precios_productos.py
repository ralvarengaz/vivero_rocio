import sqlite3

DB = "data/vivero.db"

def actualizar_precios():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Productos con precios específicos
    precios_productos = {
        "Lapacho amarillo": 45000,
        "Mango": 35000,
        "Orquídea": 55000,
        "Eucalipto": 25000,
        "Cedrón Paraguay": 18000,
    }
    
    for nombre, precio in precios_productos.items():
        cur.execute("""
            UPDATE productos 
            SET precio = ?, stock = CASE WHEN stock = 0 THEN 15 ELSE stock END
            WHERE nombre LIKE ?
        """, (precio, f'%{nombre}%'))
        print(f"✅ {nombre}: {precio:,} ₲")
    
    conn.commit()
    conn.close()
    print("🎉 Precios actualizados")

if __name__ == "__main__":
    actualizar_precios()