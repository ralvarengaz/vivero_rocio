import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import threading
import time

# ------------------------------------------------------------
# Configuración base de datos PostgreSQL en Render
# ------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "❌ No se encontró la variable DATABASE_URL. "
        "Configúrala en Render → Environment → DATABASE_URL"
    )

# Crear un pool de conexiones reutilizables
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1,               # mínimo de conexiones
        10,              # máximo de conexiones
        DATABASE_URL,
        connect_timeout=10
    )
    print("✅ Pool de conexiones PostgreSQL inicializado correctamente.")
except Exception as e:
    print(f"🚨 Error inicializando pool de PostgreSQL: {e}")
    raise

# Lock global para acceso concurrente seguro
db_lock = threading.Lock()

# ------------------------------------------------------------
# Context manager para obtener y liberar conexiones
# ------------------------------------------------------------
@contextmanager
def get_db_connection():
    """Devuelve una conexión PostgreSQL desde el pool de manera segura"""
    conn = None
    try:
        with db_lock:
            conn = db_pool.getconn()
        yield conn
    except psycopg2.OperationalError as e:
        print(f"⚠️ Error operacional de base de datos: {e}")
        time.sleep(1)
        with db_lock:
            conn = db_pool.getconn()
        yield conn
    except Exception as e:
        print(f"❌ Error inesperado con PostgreSQL: {e}")
        raise e
    finally:
        if conn:
            try:
                db_pool.putconn(conn)
            except Exception as close_error:
                print(f"⚠️ Error devolviendo conexión al pool: {close_error}")
