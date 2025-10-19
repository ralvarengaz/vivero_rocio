from modules.database_manager import get_db_connection
import flet as ft
import hashlib

def login_view(container, page: ft.Page):
    """Renderiza la vista de login y maneja autenticación con PostgreSQL"""
    
    print("🎨 Iniciando login view innovador...")

    usuario = ft.TextField(
        label="Usuario", 
        width=300, 
        autofocus=True,
        hint_text="Ingresa tu usuario",
        prefix_icon=ft.Icons.PERSON,
        border_color="#2E7D32"
    )
    
    password = ft.TextField(
        label="Contraseña", 
        width=300, 
        password=True, 
        can_reveal_password=True,
        hint_text="Ingresa tu contraseña",
        prefix_icon=ft.Icons.LOCK,
        border_color="#2E7D32"
    )
    
    mensaje = ft.Text("", color="red", size=14, weight="bold")
    
    contador_intentos = {"count": 0}

    def autenticar(e):
        contador_intentos["count"] += 1
        print(f"🔐 Intento de login #{contador_intentos['count']}: {usuario.value}")
        
        if not usuario.value or not password.value:
            mensaje.value = "❌ Por favor completa todos los campos"
            page.update()
            return
        
        try:
            # Hashear la contraseña ingresada
            password_hash = hashlib.sha256(password.value.encode()).hexdigest()
            
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Buscar usuario con contraseña hasheada
                cur.execute("""
                    SELECT id, username, nombre_completo, rol, estado 
                    FROM usuarios 
                    WHERE (username = %s OR usuario = %s) AND password = %s
                """, (usuario.value, usuario.value, password_hash))
                
                datos = cur.fetchone()

            if datos:
                user_id, username, nombre_completo, rol, estado = datos
                
                # Verificar si el usuario está activo
                if estado != 'Activo':
                    mensaje.value = "❌ Usuario inactivo. Contacta al administrador."
                    print(f"❌ Intento #{contador_intentos['count']}: Usuario inactivo")
                    page.update()
                    return
                
                # Actualizar último acceso
                try:
                    with get_db_connection() as conn:
                        cur = conn.cursor()
                        cur.execute("UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id = %s", (user_id,))
                        conn.commit()
                except Exception as update_error:
                    print(f"⚠️ Error actualizando último acceso: {update_error}")
                
                mensaje.value = ""
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"✅ Bienvenido {nombre_completo} ({rol})", color="white"),
                    bgcolor="#2E7D32",
                    duration=3000
                )
                page.snack_bar.open = True
                print(f"✅ Login exitoso #{contador_intentos['count']}: {username} - {rol}")
                page.update()
                
                # Importar dashboard y redirigir
                try:
                    from modules import dashboard
                    dashboard.dashboard_view(container, page=page)
                except Exception as dashboard_error:
                    print(f"❌ Error cargando dashboard: {dashboard_error}")
                    mensaje.value = f"❌ Error cargando sistema: {str(dashboard_error)}"
                    page.update()
            else:
                mensaje.value = "❌ Usuario o contraseña incorrectos"
                print(f"❌ Error #{contador_intentos['count']}: Credenciales inválidas")
                page.update()
                
        except Exception as err:
            mensaje.value = f"❌ Error del sistema: {err}"
            print(f"❌ Error #{contador_intentos['count']}: ❌ Error del sistema: {err}")
            import traceback
            traceback.print_exc()
            page.update()

    def on_password_submit(e):
        """Permite login al presionar Enter en el campo de contraseña"""
        autenticar(e)

    password.on_submit = on_password_submit

    btn_login = ft.ElevatedButton(
        text="Iniciar Sesión",
        icon=ft.Icons.LOGIN,
        on_click=autenticar,
        bgcolor="#2E7D32",
        color="white",
        width=300,
        height=45
    )

    # Limpiar contenedor
    container.controls.clear()
    
    # Card de login con mejor diseño
    login_card = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.ECO, size=80, color="#2E7D32"),
                    padding=ft.padding.only(bottom=10)
                ),
                ft.Text(
                    "Vivero Rocío", 
                    size=32, 
                    weight="bold",
                    color="#2E7D32",
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Sistema de Gestión", 
                    size=16, 
                    color="#666",
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=20),
                usuario,
                password,
                mensaje,
                ft.Container(height=10),
                btn_login,
                ft.Container(height=20),
                ft.Text(
                    "Usuario por defecto: admin | Contraseña: admin123",
                    size=12,
                    color="#999",
                    text_align=ft.TextAlign.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        ),
        width=400,
        padding=40,
        border_radius=15,
        bgcolor="white",
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
                colors=["#E8F5E9", "#C8E6C9"]
            )
        )
    )
    
    print("✅ Login view con mejor contraste renderizado")
    page.update()
