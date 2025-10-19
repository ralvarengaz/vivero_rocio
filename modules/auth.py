from modules.database_manager import get_db_connection
import flet as ft

def login_view(container, page: ft.Page):
    """Renderiza la vista de login y maneja autenticación"""

    usuario = ft.TextField(label="Usuario", width=300, autofocus=True)
    password = ft.TextField(label="Contraseña", width=300, password=True, can_reveal_password=True)
    mensaje = ft.Text(color="red")

    def autenticar(e):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT * FROM usuarios WHERE usuario = %s AND password = %s",
                    (usuario.value, password.value),
                )
                datos = cur.fetchone()
                cur.close()

            if datos:
                mensaje.value = ""
                page.snack_bar = ft.SnackBar(ft.Text(f"✅ Bienvenido {usuario.value}"), open=True)
                page.update()
                # Aquí puedes importar dashboard o redirigir a la vista principal
            else:
                mensaje.value = "❌ Usuario o contraseña incorrectos"
                page.update()
        except Exception as err:
            mensaje.value = f"❌ Error del sistema: {err}"
            print(f"Error obteniendo usuarios: {err}")
            page.update()

    btn_login = ft.ElevatedButton(text="Iniciar Sesión", icon=ft.icons.LOGIN, on_click=autenticar)

    container.controls.clear()
    container.controls.append(
        ft.Column(
            [
                ft.Text("Vivero Rocío", size=24, weight="bold"),
                usuario,
                password,
                mensaje,
                btn_login,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )
    page.update()
