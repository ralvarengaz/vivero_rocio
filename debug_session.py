from session_manager import session

def debug_session():
    print("🔍 === DEBUG SESIÓN ===")
    
    # Verificar sesión
    print(f"¿Sesión activa?: {session.is_logged_in()}")
    print(f"Usuario actual: {session.get_current_user()}")
    
    # Verificar si hay instancia
    print(f"Instancia session: {session}")
    print(f"Tipo de session: {type(session)}")
    
    # Verificar atributos
    if hasattr(session, '_current_user'):
        print(f"_current_user: {session._current_user}")
    
    # Intentar login manual para probar
    try:
        test_user = {
            'id': 1,
            'username': 'admin',
            'nombre_completo': 'Administrador',
            'rol': 'Administrador'
        }
        session.login(test_user)
        print(f"✅ Login manual exitoso: {session.get_current_user()}")
    except Exception as e:
        print(f"❌ Error en login manual: {e}")

if __name__ == "__main__":
    debug_session()