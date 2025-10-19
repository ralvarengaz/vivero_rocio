import os
import flet as ft

# Detectar entorno de Render
if os.environ.get("RENDER") or os.environ.get("RENDER_INTERNAL_HOSTNAME"):
    DB_PATH = "/tmp/vivero.db"
else:
    DB_PATH = "data/vivero.db"

print(f"🔍 Usando base de datos en: {DB_PATH}")

# --- Migraciones automáticas ---
try:
    from modules.migrations import ensure_schema
    ensure_schema(DB_PATH)
except Exception as _e:
    print("🚨 Aviso: no se pudo ejecutar migraciones:", _e)

from modules import auth

def main(page: ft.Page):
    page.title = "Vivero Rocío - Sistema de Gestión"
    page.theme_mode = "light"
    page.window_maximized = True
    page.padding = 0
    page.spacing = 0

    main_content = ft.Column(expand=True)
    page.add(main_content)
    auth.login_view(main_content, page=page)

if __name__ == "__main__":
    print("🌱 Iniciando aplicación Vivero Rocío...")
    port = int(os.environ.get("PORT", "8550"))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=port)
