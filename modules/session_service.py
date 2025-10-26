"""
Servicio de gestión de sesiones de usuario
Reemplazo mejorado y seguro de session_manager.py
"""
from typing import Optional, Dict, Any, List
from modules.db_service import db


class SessionService:
    """
    Servicio singleton para gestión de sesiones de usuario
    """
    _instance = None
    _current_user: Optional[Dict[str, Any]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def login(self, user_data: Dict[str, Any]) -> bool:
        """
        Inicia sesión y carga permisos del usuario

        Args:
            user_data: Diccionario con datos del usuario (id, username, rol, etc.)

        Returns:
            True si el login fue exitoso
        """
        try:
            # Guardar datos del usuario
            self._current_user = user_data.copy()

            # Cargar permisos
            permisos = self._cargar_permisos(user_data['id'])
            self._current_user['permisos'] = permisos

            print(f"✅ Sesión iniciada: {user_data.get('username')} ({user_data.get('rol')})")
            return True
        except Exception as e:
            print(f"❌ Error iniciando sesión: {e}")
            return False

    def logout(self):
        """Cierra la sesión actual"""
        if self._current_user:
            print(f"🚪 Sesión cerrada: {self._current_user.get('username')}")
        self._current_user = None

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Obtiene el usuario actual"""
        return self._current_user

    def is_logged_in(self) -> bool:
        """Verifica si hay un usuario logueado"""
        return self._current_user is not None

    def _cargar_permisos(self, user_id: int) -> Dict[str, Dict[str, bool]]:
        """
        Carga permisos del usuario desde la base de datos

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario de permisos por módulo
        """
        try:
            query = """
                SELECT modulo, puede_ver, puede_crear, puede_editar, puede_eliminar
                FROM permisos_usuario
                WHERE usuario_id = %s
            """

            permisos_raw = db.execute_query(query, (user_id,), fetch="all")

            permisos = {}
            for row in permisos_raw:
                if db.db_type == "postgresql":
                    modulo, ver, crear, editar, eliminar = row
                else:
                    # SQLite con row_factory
                    modulo = row[0]
                    ver, crear, editar, eliminar = row[1], row[2], row[3], row[4]

                permisos[modulo] = {
                    'ver': bool(ver),
                    'crear': bool(crear),
                    'editar': bool(editar),
                    'eliminar': bool(eliminar)
                }

            return permisos
        except Exception as e:
            print(f"⚠️ Error cargando permisos: {e}")
            return {}

    def tiene_permiso(self, modulo: str, accion: str = 'ver') -> bool:
        """
        Verifica si el usuario actual tiene permiso para una acción específica

        Args:
            modulo: Nombre del módulo (productos, clientes, etc.)
            accion: Acción a verificar (ver, crear, editar, eliminar)

        Returns:
            True si tiene permiso, False en caso contrario
        """
        if not self.is_logged_in():
            return False

        # Administradores tienen acceso total
        if self._current_user.get('rol') == 'Administrador':
            return True

        # Verificar permisos específicos
        permisos_modulo = self._current_user.get('permisos', {}).get(modulo, {})
        return permisos_modulo.get(accion, False)

    def get_modulos_permitidos(self) -> List[str]:
        """
        Obtiene lista de módulos a los que el usuario tiene acceso (ver)

        Returns:
            Lista de nombres de módulos permitidos
        """
        if not self.is_logged_in():
            return []

        # Administradores ven todos los módulos
        if self._current_user.get('rol') == 'Administrador':
            return ['productos', 'clientes', 'proveedores', 'pedidos', 'ventas', 'reportes', 'usuarios']

        # Obtener módulos con permiso de ver
        modulos_permitidos = []
        permisos = self._current_user.get('permisos', {})

        for modulo, permisos_modulo in permisos.items():
            if permisos_modulo.get('ver', False):
                modulos_permitidos.append(modulo)

        return modulos_permitidos

    def get_user_id(self) -> Optional[int]:
        """Obtiene el ID del usuario actual"""
        return self._current_user.get('id') if self._current_user else None

    def get_username(self) -> Optional[str]:
        """Obtiene el username del usuario actual"""
        return self._current_user.get('username') if self._current_user else None

    def get_user_role(self) -> Optional[str]:
        """Obtiene el rol del usuario actual"""
        return self._current_user.get('rol') if self._current_user else None

    def get_user_fullname(self) -> Optional[str]:
        """Obtiene el nombre completo del usuario actual"""
        return self._current_user.get('nombre_completo') if self._current_user else None

    def is_admin(self) -> bool:
        """Verifica si el usuario actual es administrador"""
        return self.get_user_role() == 'Administrador'

    def refresh_permissions(self):
        """Recarga los permisos del usuario actual"""
        if not self.is_logged_in():
            return

        user_id = self.get_user_id()
        permisos = self._cargar_permisos(user_id)
        self._current_user['permisos'] = permisos
        print(f"✅ Permisos recargados para usuario ID: {user_id}")


# Instancia global del servicio de sesión
session = SessionService()
