"""
Tests para el servicio de autenticación (auth_service.py)
"""
import pytest
import bcrypt
from modules.auth_service import hash_password, verify_password


class TestAuthService:
    """Tests para autenticación"""

    def test_hash_password(self):
        """Verifica que hash_password crea un hash válido"""
        password = "test123"
        hashed = hash_password(password)
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password

    def test_verify_password_correcto(self):
        """Verifica que verify_password acepta contraseña correcta"""
        password = "test123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) == True

    def test_verify_password_incorrecto(self):
        """Verifica que verify_password rechaza contraseña incorrecta"""
        password = "test123"
        hashed = hash_password(password)
        assert verify_password("wrong", hashed) == False

    def test_hash_diferentes_para_misma_password(self):
        """Verifica que bcrypt genera hashes diferentes con salt"""
        password = "test123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # Los hashes deben ser diferentes debido al salt
        assert hash1 != hash2
        # Pero ambos deben verificar correctamente
        assert verify_password(password, hash1) == True
        assert verify_password(password, hash2) == True
