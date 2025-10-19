import flet as ft
# --- Migraciones automáticas ---
try:
    from modules.migrations import ensure_schema
    ensure_schema("data/vivero.db")
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

    # Contenedor principal usando Column
    main_content = ft.Column(expand=True)
    
    # Agregar a la página
    page.add(main_content)
    
    # Iniciar con login
    print("🔐 Iniciando vista de login...")
    auth.login_view(main_content, page=page)

if __name__ == "__main__":
    print("🌱 Iniciando aplicación Vivero Rocío...")
    ft.app(target=main)
    if __name__ == "__main__":
        import os
        import flet as ft
        port = int(os.environ.get("PORT", "8550"))
        ft.app(
            target=main,
            view=ft.AppView.WEB_BROWSER,  # Servir como web
            host="0.0.0.0",
            port=port
        )
