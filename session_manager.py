# Compatibilidad hacia atrás - Importar desde session_service
from modules.session_service import session, SessionService

# Alias para compatibilidad
SessionManager = SessionService

print("✅ session_manager.py cargado (usando session_service)")