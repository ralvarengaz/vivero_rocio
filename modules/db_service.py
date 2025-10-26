"""
Servicio de base de datos unificado
Maneja conexiones PostgreSQL y SQLite de forma transparente
"""
import os
import psycopg2
import sqlite3
from psycopg2 import pool
from contextlib import contextmanager
from threading import Lock
from typing import Optional, Any, Tuple, List
from modules.config import DATABASE_URL, DB_POOL_MIN, DB_POOL_MAX, DB_TIMEOUT


class DatabaseService:
    """
    Servicio singleton para manejo de conexiones a base de datos
    Soporta PostgreSQL (producción) y SQLite (desarrollo)
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.db_url = DATABASE_URL
        self.db_type = self._detect_db_type()
        self.pool = None

        # Inicializar pool si es PostgreSQL
        if self.db_type == "postgresql":
            self._init_postgres_pool()
        else:
            print("⚠️ Usando SQLite - Solo para desarrollo")

        self._initialized = True

    def _detect_db_type(self) -> str:
        """Detecta el tipo de base de datos"""
        if self.db_url.startswith("postgresql") or self.db_url.startswith("postgres"):
            return "postgresql"
        elif self.db_url.startswith("sqlite"):
            return "sqlite"
        else:
            # Por defecto PostgreSQL
            return "postgresql"

    def _init_postgres_pool(self):
        """Inicializa el pool de conexiones PostgreSQL"""
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                DB_POOL_MIN,
                DB_POOL_MAX,
                self.db_url,
                connect_timeout=DB_TIMEOUT
            )
            print("✅ Pool PostgreSQL inicializado")
        except Exception as e:
            print(f"❌ Error inicializando pool PostgreSQL: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        Context manager para obtener conexión a la BD
        Funciona tanto con PostgreSQL como SQLite
        """
        conn = None
        try:
            if self.db_type == "postgresql":
                # Obtener conexión del pool
                with self._lock:
                    conn = self.pool.getconn()
                conn.autocommit = False  # Transacciones explícitas
                yield conn
            else:
                # SQLite
                db_path = self.db_url.replace("sqlite:///", "")
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row  # Acceso por nombre de columna
                yield conn

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ Error en conexión BD: {e}")
            raise

        finally:
            if conn:
                try:
                    if self.db_type == "postgresql":
                        # Devolver al pool
                        self.pool.putconn(conn)
                    else:
                        # Cerrar SQLite
                        conn.close()
                except Exception as close_error:
                    print(f"⚠️ Error cerrando conexión: {close_error}")

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch: str = "all"
    ) -> Any:
        """
        Ejecuta una query SELECT y retorna resultados

        Args:
            query: Query SQL
            params: Parámetros de la query
            fetch: 'one', 'all' o 'none'

        Returns:
            Resultados de la query
        """
        with self.get_connection() as conn:
            cur = conn.cursor()

            # Adaptar query para SQLite vs PostgreSQL
            if self.db_type == "sqlite":
                query = self._adapt_query_to_sqlite(query)
                params = params or ()
            else:
                params = params or ()

            cur.execute(query, params)

            if fetch == "one":
                result = cur.fetchone()
            elif fetch == "all":
                result = cur.fetchall()
            else:
                result = None

            cur.close()
            return result

    def execute_command(
        self,
        command: str,
        params: Optional[Tuple] = None,
        commit: bool = True
    ) -> Optional[int]:
        """
        Ejecuta un comando INSERT/UPDATE/DELETE

        Args:
            command: Comando SQL
            params: Parámetros del comando
            commit: Si debe hacer commit automáticamente

        Returns:
            ID del registro insertado (si aplica) o número de filas afectadas
        """
        with self.get_connection() as conn:
            cur = conn.cursor()

            # Adaptar comando para SQLite vs PostgreSQL
            if self.db_type == "sqlite":
                command = self._adapt_query_to_sqlite(command)
                params = params or ()
            else:
                params = params or ()

            cur.execute(command, params)

            # Obtener ID insertado si es un INSERT
            last_id = None
            if command.strip().upper().startswith("INSERT"):
                if self.db_type == "postgresql":
                    # PostgreSQL con RETURNING
                    if "RETURNING" in command.upper():
                        result = cur.fetchone()
                        last_id = result[0] if result else None
                    else:
                        # Intentar obtener el último ID
                        try:
                            cur.execute("SELECT lastval()")
                            last_id = cur.fetchone()[0]
                        except:
                            last_id = None
                else:
                    # SQLite
                    last_id = cur.lastrowid

            rowcount = cur.rowcount

            if commit:
                conn.commit()

            cur.close()
            return last_id if last_id else rowcount

    def execute_many(
        self,
        command: str,
        params_list: List[Tuple],
        commit: bool = True
    ) -> int:
        """
        Ejecuta un comando múltiples veces con diferentes parámetros

        Args:
            command: Comando SQL
            params_list: Lista de tuplas de parámetros
            commit: Si debe hacer commit automáticamente

        Returns:
            Número de filas afectadas
        """
        with self.get_connection() as conn:
            cur = conn.cursor()

            # Adaptar comando
            if self.db_type == "sqlite":
                command = self._adapt_query_to_sqlite(command)

            cur.executemany(command, params_list)
            rowcount = cur.rowcount

            if commit:
                conn.commit()

            cur.close()
            return rowcount

    def _adapt_query_to_sqlite(self, query: str) -> str:
        """
        Adapta una query de PostgreSQL a SQLite
        """
        # Reemplazar placeholders de PostgreSQL (%s) por SQLite (?)
        # NOTA: Esta es una conversión simple, puede necesitar ajustes
        adapted = query.replace("%s", "?")

        # Reemplazar funciones específicas de PostgreSQL
        adapted = adapted.replace("CURRENT_TIMESTAMP", "datetime('now')")
        adapted = adapted.replace("CURRENT_DATE", "date('now')")
        adapted = adapted.replace("COALESCE", "IFNULL")

        # Reemplazar tipos de datos
        adapted = adapted.replace("SERIAL", "INTEGER")
        adapted = adapted.replace("VARCHAR", "TEXT")
        adapted = adapted.replace("INTEGER PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")

        return adapted

    @contextmanager
    def transaction(self):
        """
        Context manager para transacciones explícitas
        """
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"❌ Error en transacción: {e}")
                raise

    def close(self):
        """Cierra el pool de conexiones"""
        if self.pool and self.db_type == "postgresql":
            self.pool.closeall()
            print("✅ Pool de conexiones cerrado")


# Instancia global del servicio
db = DatabaseService()


# Funciones de conveniencia para compatibilidad hacia atrás
@contextmanager
def get_db_connection():
    """
    Función de conveniencia para obtener conexión
    Compatible con código existente
    """
    with db.get_connection() as conn:
        yield conn
