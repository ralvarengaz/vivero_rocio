# Compatibilidad hacia atrás - Importar desde db_service
from modules.db_service import get_db_connection, db

# Mantener variables para compatibilidad
DATABASE_URL = db.db_url
db_pool = db.pool if db.db_type == "postgresql" else None

print("✅ database_manager.py cargado (usando db_service)")
