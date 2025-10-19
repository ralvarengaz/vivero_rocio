import sqlite3
import os
import time

DB = "data/vivero.db"

def reparar_base_datos():
    """Repara y optimiza la base de datos"""
    print("🔧 Reparando base de datos...")
    
    try:
        # Verificar si existe archivo de lock y eliminarlo
        lock_files = [f"{DB}-wal", f"{DB}-shm", f"{DB}-journal"]
        for lock_file in lock_files:
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                    print(f"🗑️ Eliminado archivo de lock: {lock_file}")
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar {lock_file}: {e}")
        
        # Conectar y optimizar
        conn = sqlite3.connect(DB, timeout=60)
        
        # Configurar WAL mode
        conn.execute("PRAGMA journal_mode=WAL")
        print("✅ Modo WAL activado")
        
        # Verificar integridad
        result = conn.execute("PRAGMA integrity_check").fetchone()
        if result[0] == "ok":
            print("✅ Integridad de la base de datos: OK")
        else:
            print(f"❌ Problema de integridad: {result[0]}")
        
        # Optimizar
        conn.execute("VACUUM")
        print("✅ Base de datos optimizada")
        
        # Reindexar
        conn.execute("REINDEX")
        print("✅ Índices reconstruidos")
        
        conn.close()
        print("🎉 Reparación completada")
        
    except Exception as e:
        print(f"❌ Error reparando BD: {e}")

if __name__ == "__main__":
    reparar_base_datos()