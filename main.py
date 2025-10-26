import os
import flet as ft

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Configuración de base de datos
DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    print("⚠️ No se encontró DATABASE_URL, usando SQLite local para desarrollo.")
    DB_URL = "sqlite:///data/vivero.db"
    os.makedirs("data", exist_ok=True)

print(f"🔗 Conectando a la base: {DB_URL}")

# Aplicar migraciones de base de datos
try:
    from modules.migrations_new import ensure_schema
    # force_recreate=False para producción (no elimina datos)
    # force_recreate=True solo para desarrollo (elimina y recrea todo)
    is_development = DB_URL.startswith("sqlite")
    ensure_schema(force_recreate=False)  # Cambiar a True solo para desarrollo
except Exception as e:
    print(f"🚨 Error al ejecutar migraciones: {e}")
    import traceback
    traceback.print_exc()

# Importar módulo de autenticación
from modules import auth_service

def main(page: ft.Page):
    """Función principal de la aplicación"""
    page.title = "Vivero Rocío - Sistema de Gestión v2.0"
    page.theme_mode = "light"
    page.window.maximized = True
    page.padding = 0
    page.spacing = 0

    # Contenedor principal
    main_content = ft.Column(expand=True)
    page.add(main_content)

    # Mostrar vista de login
    auth_service.login_view(main_content, page=page)

if __name__ == "__main__":
    print("🌱 Iniciando Vivero Rocío v2.0 (Sistema Optimizado)...")
    port = int(os.environ.get("PORT", "8550"))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=port)
