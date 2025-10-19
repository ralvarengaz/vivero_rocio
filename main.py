import os
import flet as ft

# --- Determinar ruta correcta de base de datos ---
if os.environ.get("RENDER") or os.environ.get("RENDER_INTERNAL_HOSTNAME"):
    DB_DIR = "/tmp"
else:
    DB_DIR = "data"

DB_PATH = os.path.join(DB_DIR, "vivero.db")

# Crear directorio de base de datos si no existe
try:
    os.makedirs(DB_DIR, exist_ok=True)
    print(f"📁 Directorio de base de datos asegurado: {DB_DIR}")
except Exception as e:
    print(f"⚠️ No se pudo crear el directorio {DB_DIR}: {e}")

# --- Migraciones automáticas ---
try:
    from modules.migrations import ensure_schema
    ensure_schema(DB_PATH)
    print(f"✅ Migraciones ejecutadas sobre: {DB_PATH}")
except Exception as _e:
    print("🚨 Aviso: no se pudo ejecutar migraciones:", _e)

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
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=port
    )
