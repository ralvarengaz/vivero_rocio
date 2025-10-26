"""
Servicio de autenticación con bcrypt
Reemplazo seguro de auth.py
"""
import bcrypt
import flet as ft
from modules.db_service import db
from modules.session_service import session
from modules.config import Colors, FontSizes, Messages, MAX_LOGIN_ATTEMPTS


def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt

    Args:
        password: Contraseña en texto plano

    Returns:
        Hash de la contraseña
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifica una contraseña contra su hash

    Args:
        password: Contraseña en texto plano
        password_hash: Hash almacenado

    Returns:
        True si la contraseña es correcta
    """
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception as e:
        print(f"Error verificando contraseña: {e}")
        return False


def authenticate_user(username: str, password: str) -> dict:
    """
    Autentica un usuario

    Args:
        username: Nombre de usuario
        password: Contraseña

    Returns:
        Diccionario con datos del usuario si la autenticación es exitosa, None si falla
    """
    try:
        query = """
            SELECT id, username, password, nombre_completo, email, rol, estado
            FROM usuarios
            WHERE username = %s
        """

        result = db.execute_query(query, (username,), fetch="one")

        if not result:
            return None

        # Extraer datos
        if db.db_type == "postgresql":
            user_id, username, password_hash, nombre_completo, email, rol, estado = result
        else:
            user_id = result[0]
            username = result[1]
            password_hash = result[2]
            nombre_completo = result[3]
            email = result[4]
            rol = result[5]
            estado = result[6]

        # Verificar estado
        if estado != 'Activo':
            return {'error': 'Usuario inactivo. Contacta al administrador.'}

        # Verificar contraseña
        if not verify_password(password, password_hash):
            return None

        # Actualizar último acceso
        update_query = """
            UPDATE usuarios
            SET ultimo_acceso = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        db.execute_command(update_query, (user_id,))

        # Retornar datos del usuario
        return {
            'id': user_id,
            'username': username,
            'nombre_completo': nombre_completo,
            'email': email,
            'rol': rol,
            'estado': estado
        }

    except Exception as e:
        print(f"Error autenticando usuario: {e}")
        return None


def login_view(container, page: ft.Page):
    """Renderiza la vista de login moderna y segura"""

    print("🎨 Iniciando vista de login...")

    # Campos de entrada
    usuario_field = ft.TextField(
        label="Usuario",
        width=300,
        autofocus=True,
        hint_text="Ingresa tu usuario",
        prefix_icon=ft.icons.PERSON,
        border_color=Colors.PRIMARY,
        focused_border_color=Colors.PRIMARY_LIGHT,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY)
    )

    password_field = ft.TextField(
        label="Contraseña",
        width=300,
        password=True,
        can_reveal_password=True,
        hint_text="Ingresa tu contraseña",
        prefix_icon=ft.icons.LOCK,
        border_color=Colors.PRIMARY,
        focused_border_color=Colors.PRIMARY_LIGHT,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY)
    )

    mensaje = ft.Text("", color=Colors.ERROR, size=FontSizes.SMALL, weight="bold")

    # Contador de intentos
    intentos = {"count": 0}

    def autenticar(e):
        """Maneja el proceso de autenticación"""
        intentos["count"] += 1

        # Validar campos vacíos
        if not usuario_field.value or not password_field.value:
            mensaje.value = Messages.WARNING_EMPTY_FIELDS
            page.update()
            return

        # Verificar límite de intentos
        if intentos["count"] > MAX_LOGIN_ATTEMPTS:
            mensaje.value = f"❌ Demasiados intentos fallidos. Espera {LOGIN_TIMEOUT_MINUTES} minutos."
            page.update()
            return

        try:
            # Autenticar usuario
            user_data = authenticate_user(usuario_field.value, password_field.value)

            if not user_data:
                mensaje.value = Messages.ERROR_LOGIN
                print(f"❌ Intento fallido #{intentos['count']}: Credenciales inválidas")
                page.update()
                return

            # Verificar si el usuario está inactivo
            if 'error' in user_data:
                mensaje.value = f"❌ {user_data['error']}"
                page.update()
                return

            # Login exitoso - iniciar sesión
            session.login(user_data)

            # Mostrar mensaje de bienvenida
            mensaje.value = ""
            page.snack_bar = ft.SnackBar(
                ft.Text(f"✅ Bienvenido {user_data['nombre_completo']} ({user_data['rol']})", color="white"),
                bgcolor=Colors.SUCCESS,
                duration=3000
            )
            page.snack_bar.open = True
            print(f"✅ Login exitoso: {user_data['username']} - {user_data['rol']}")
            page.update()

            # Redirigir al dashboard
            try:
                from modules import dashboard
                dashboard.dashboard_view(container, page=page)
            except Exception as dashboard_error:
                print(f"❌ Error cargando dashboard: {dashboard_error}")
                mensaje.value = f"{Messages.ERROR_CONNECTION}"
                page.update()

        except Exception as err:
            mensaje.value = f"{Messages.ERROR_CONNECTION}"
            print(f"❌ Error en autenticación: {err}")
            import traceback
            traceback.print_exc()
            page.update()

    def on_password_submit(e):
        """Permite login al presionar Enter"""
        autenticar(e)

    password_field.on_submit = on_password_submit

    # Botón de login
    btn_login = ft.ElevatedButton(
        text="Iniciar Sesión",
        icon=ft.icons.LOGIN,
        on_click=autenticar,
        bgcolor=Colors.PRIMARY,
        color="white",
        width=300,
        height=45,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8)
        )
    )

    # Limpiar contenedor
    container.controls.clear()

    # Card de login con diseño mejorado
    login_card = ft.Container(
        content=ft.Column(
            [
                # Logo/Icono
                ft.Container(
                    content=ft.Icon(ft.icons.ECO, size=80, color=Colors.PRIMARY),
                    padding=ft.padding.only(bottom=10)
                ),
                # Título
                ft.Text(
                    "Vivero Rocío",
                    size=FontSizes.XXLARGE,
                    weight="bold",
                    color=Colors.PRIMARY,
                    text_align=ft.TextAlign.CENTER
                ),
                # Subtítulo
                ft.Text(
                    "Sistema de Gestión Integral",
                    size=FontSizes.MEDIUM,
                    color=Colors.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=20),
                # Campos
                usuario_field,
                password_field,
                mensaje,
                ft.Container(height=10),
                # Botón
                btn_login,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        ),
        width=400,
        padding=40,
        border_radius=15,
        bgcolor=Colors.BG_WHITE,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.colors.with_opacity(0.3, "black"),
            offset=ft.Offset(0, 4)
        )
    )

    # Centrar el card en la página
    container.controls.append(
        ft.Container(
            content=login_card,
            alignment=ft.alignment.center,
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[Colors.GRADIENT_START, Colors.GRADIENT_END]
            )
        )
    )

    print("✅ Vista de login renderizada")
    page.update()
