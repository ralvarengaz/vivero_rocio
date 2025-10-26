"""
Tests para el servicio de sesiones (session_service.py)
"""
import pytest
from modules.session_service import SessionService, session


class TestSessionService:
    """Tests para el servicio de sesiones"""

    def setup_method(self):
        """Limpia la sesión antes de cada test"""
        session.logout()

    def test_session_singleton(self):
        """Verifica que session es un singleton"""
        session1 = SessionService()
        session2 = SessionService()
        assert session1 is session2

    def test_login_logout(self):
        """Verifica login y logout"""
        user_data = {
            'id': 1,
            'username': 'test',
            'rol': 'Usuario',
            'nombre_completo': 'Test User'
        }

        # Login
        result = session.login(user_data)
        assert result == True
        assert session.is_logged_in() == True
        assert session.get_current_user() is not None

        # Logout
        session.logout()
        assert session.is_logged_in() == False
        assert session.get_current_user() is None

    def test_get_user_info(self):
        """Verifica obtención de información del usuario"""
        user_data = {
            'id': 1,
            'username': 'testuser',
            'rol': 'Vendedor',
            'nombre_completo': 'Test User'
        }

        session.login(user_data)

        assert session.get_user_id() == 1
        assert session.get_username() == 'testuser'
        assert session.get_user_role() == 'Vendedor'
        assert session.get_user_fullname() == 'Test User'

    def test_admin_permissions(self):
        """Verifica que Administrador tiene todos los permisos"""
        user_data = {
            'id': 1,
            'username': 'admin',
            'rol': 'Administrador',
            'nombre_completo': 'Admin'
        }

        session.login(user_data)

        # Admin debe tener todos los permisos
        assert session.tiene_permiso('productos', 'ver') == True
        assert session.tiene_permiso('productos', 'crear') == True
        assert session.tiene_permiso('productos', 'editar') == True
        assert session.tiene_permiso('productos', 'eliminar') == True
        assert session.is_admin() == True

    def test_non_admin_without_permissions(self):
        """Verifica que usuario sin permisos no tiene acceso"""
        user_data = {
            'id': 2,
            'username': 'user',
            'rol': 'Usuario',
            'nombre_completo': 'Regular User'
        }

        session.login(user_data)
        session._current_user['permisos'] = {}  # Sin permisos

        # Usuario sin permisos no debe tener acceso
        assert session.tiene_permiso('productos', 'ver') == False
        assert session.is_admin() == False
