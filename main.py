import os
import flet as ft

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    print("⚠️ No se encontró DATABASE_URL, usando SQLite local.")
    DB_URL = "sqlite:///data/vivero.db"

print(f"🔗 Conectando a la base: {DB_URL}")

try:
    from modules.migrations import ensure_schema
    ensure_schema(DB_URL)
except Exception as e:
    print("🚨 Error al ejecutar migraciones:", e)

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
