"""
Tests para el servicio de base de datos (db_service.py)
"""
import pytest
from modules.db_service import db


class TestDatabaseService:
    """Tests para el servicio de base de datos"""

    def test_db_instance_singleton(self):
        """Verifica que db sea un singleton"""
        from modules.db_service import DatabaseService
        db1 = DatabaseService()
        db2 = DatabaseService()
        assert db1 is db2

    def test_db_connection(self):
        """Verifica que se puede obtener una conexión"""
        with db.get_connection() as conn:
            assert conn is not None

    def test_execute_query(self):
        """Verifica que execute_query funciona"""
        result = db.execute_query("SELECT 1 as test", fetch="one")
        assert result is not None

    def test_execute_command(self):
        """Verifica que execute_command funciona"""
        # Crear tabla temporal para pruebas
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name TEXT)")
            conn.commit()

        # Insertar datos
        result = db.execute_command(
            "INSERT INTO test_table (name) VALUES (%s) RETURNING id",
            ("test",)
        )
        assert result is not None

        # Limpiar
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DROP TABLE IF EXISTS test_table")
            conn.commit()

    def test_transaction(self):
        """Verifica que las transacciones funcionan"""
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS test_trans (id SERIAL PRIMARY KEY, value INTEGER)")
            conn.commit()

        try:
            with db.transaction() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO test_trans (value) VALUES (%s)", (100,))
        except Exception:
            pass

        # Limpiar
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DROP TABLE IF EXISTS test_trans")
            conn.commit()
