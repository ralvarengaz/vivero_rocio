import sqlite3
import time
import threading
from contextlib import contextmanager

DB = "data/vivero.db"

# Lock global para evitar accesos concurrentes
db_lock = threading.Lock()

@contextmanager
def get_db_connection(timeout=30):
    """Context manager para manejo seguro de conexiones SQLite"""
    conn = None
    try:
        # Usar lock para evitar accesos concurrentes
        with db_lock:
            conn = sqlite3.connect(DB, timeout=timeout)
            conn.execute("PRAGMA journal_mode=WAL")  # Permite lecturas concurrentes
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance entre velocidad y seguridad
            conn.execute("PRAGMA temp_store=MEMORY")  # Usar memoria para operaciones temporales
            conn.execute("PRAGMA cache_size=10000")  # Cache más grande
            yield conn
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print(f"⚠️ Base de datos bloqueada, reintentando en 1 segundo...")
            time.sleep(1)
            # Reintentar una vez
            try:
                conn = sqlite3.connect(DB, timeout=timeout)
                conn.execute("PRAGMA journal_mode=WAL")
                yield conn
            except Exception as retry_error:
                print(f"❌ Error después del reintento: {retry_error}")
                raise retry_error
        else:
            print(f"❌ Error de base de datos: {e}")
            raise e
    except Exception as e:
        print(f"❌ Error inesperado con la base de datos: {e}")
        raise e
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                print(f"⚠️ Error cerrando conexión: {close_error}")