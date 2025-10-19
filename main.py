import os
import flet as ft

# --- Ajuste de ruta de base de datos ---
# Si estamos en Render, usar /tmp (único directorio escribible)
if os.environ.get("RENDER") or os.environ.get("RENDER_INTERNAL_HOSTNAME"):
    DB_PATH = os.path.join("/tmp", "vivero.db")
else:
    DB_PATH = os.path.join("data", "vivero.db")

# Crear carpeta si no existe
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# --- Migraciones automáticas ---
try:
    from modules.migrations import ensure_schema
    ensure_schema(DB_PATH)
except Exception as _e:
    print("Aviso: no se pudo ejecutar migraciones:", _e)

from modules import auth


def main(page: ft.Page):
    # Configuración de la página
    page.title = "Vivero Rocío - Sistema de Gestión"
    page.theme_mode = "light"
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    page.window_maximized = True
    page.padding = 0
    page.spacing = 0

    print("🚀 Configurando página principal...")

    # Contenedor principal
    main_content = ft.Column(expand=True)
    page.add(main_content)

    # Iniciar login
    print("🔐 Iniciando vista de login...")
    auth.login_view(main_content, page=page)


if __name__ == "__main__":
    print("🌱 Iniciando aplicación Vivero Rocío...")
    port = int(os.environ.get("PORT", "8550"))
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,  # Servir como web
        host="0.0.0.0",
        port=port
    )
