import sqlite3
from datetime import datetime

DB = "data/vivero.db"

class SessionManager:
    _instance = None
    _current_user = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def login(self, user_data):
        """Inicia sesión y carga permisos del usuario"""
        self._current_user = user_data
        try:
            self._current_user['permisos'] = self.cargar_permisos(user_data['id'])
        except:
            # Si no hay tabla permisos, dar acceso básico
            self._current_user['permisos'] = {}
        print(f"✅ Sesión iniciada: {user_data['username']} ({user_data['rol']})")
        return True
    
    def logout(self):
        """Cierra la sesión actual"""
        if self._current_user:
            print(f"🚪 Sesión cerrada: {self._current_user['username']}")
        self._current_user = None
    
    def get_current_user(self):
        """Obtiene el usuario actual"""
        return self._current_user
    
    def is_logged_in(self):
        """Verifica si hay un usuario logueado"""
        return self._current_user is not None
    
    def cargar_permisos(self, user_id):
        """Carga permisos del usuario desde la base de datos"""
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT modulo, puede_ver, puede_crear, puede_editar, puede_eliminar
                FROM permisos_usuario 
                WHERE usuario_id = ?
            """, (user_id,))
            
            permisos_raw = cur.fetchall()
            conn.close()
            
            permisos = {}
            for modulo, ver, crear, editar, eliminar in permisos_raw:
                permisos[modulo] = {
                    'ver': bool(ver),
                    'crear': bool(crear),
                    'editar': bool(editar),
                    'eliminar': bool(eliminar)
                }
            
            return permisos
        except:
            conn.close()
            return {}
    
    def tiene_permiso(self, modulo, accion='ver'):
        """Verifica si el usuario actual tiene permiso para una acción específica"""
        if not self.is_logged_in():
            return False
        
        # Administradores tienen acceso total
        if self._current_user.get('rol') == 'Administrador':
            return True
        
        # Verificar permisos específicos
        permisos_modulo = self._current_user.get('permisos', {}).get(modulo, {})
        return permisos_modulo.get(accion, False)
    
    def get_modulos_permitidos(self):
        """Obtiene lista de módulos a los que el usuario tiene acceso (ver)"""
        if not self.is_logged_in():
            return []
        
        # Administradores ven todos los módulos
        if self._current_user.get('rol') == 'Administrador':
            return ['productos', 'clientes', 'proveedores', 'pedidos', 'ventas', 'reportes', 'usuarios']
        
        modulos_permitidos = []
        permisos = self._current_user.get('permisos', {})
        
        for modulo, permisos_modulo in permisos.items():
            if permisos_modulo.get('ver', False):
                modulos_permitidos.append(modulo)
        
        return modulos_permitidos

# Instancia global del gestor de sesión
session = SessionManager()