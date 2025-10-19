from modules.database_manager import get_db_connection
import flet as ft
import hashlib

def login_view(container, page: ft.Page):
    """Renderiza la vista de login y maneja autenticación"""
    
    print("🎨 Iniciando login view innovador...")

    usuario = ft.TextField(
        label="Usuario", 
        width=300, 
        autofocus=True,
        border_color="#2E7D32",
        focused_border_color="#66BB6A"
    )
    password = ft.TextField(
        label="Contraseña", 
        width=300, 
        password=True, 
        can_reveal_password=True,
        border_color="#2E7D32",
        focused_border_color="#66BB6A"
    )
    mensaje = ft.Text(color="red", size=14)
    
    contador_intentos = {"valor": 0}

    def autenticar(e):
        """Autentica usuario contra PostgreSQL"""
        contador_intentos["valor"] += 1
        print(f"🔐 Intento de login #{contador_intentos['valor']}: {usuario.value}")
        
        if not usuario.value or not password.value:
            mensaje.value = "❌ Por favor complete todos los campos"
            page.update()
            return
        
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Buscar usuario por username o usuario
                cur.execute(
                    """SELECT id, username, password, nombre_completo, rol, estado 
                       FROM usuarios 
                       WHERE (username = %s OR usuario = %s) AND estado = 'Activo'""",
                    (usuario.value, usuario.value)
                )
                datos = cur.fetchone()
                
                if datos:
                    user_id, username, password_hash, nombre_completo, rol, estado = datos
                    
                    # Verificar contraseña (SHA256)
                    password_ingresada = hashlib.sha256(password.value.encode()).hexdigest()
                    
                    if password_ingresada == password_hash:
                        print(f"✅ Login exitoso para: {username} ({rol})")
                        mensaje.value = ""
                        
                        # Guardar sesión
                        page.session.set("user_id", user_id)
                        page.session.set("username", username)
                        page.session.set("nombre_completo", nombre_completo)
                        page.session.set("rol", rol)
                        
                        # Actualizar último acceso
                        cur.execute(
                            "UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id = %s",
                            (user_id,)
                        )
                        conn.commit()
                        
                        page.snack_bar = ft.SnackBar(
                            ft.Text(f"✅ Bienvenido {nombre_completo}"), 
                            open=True,
                            bgcolor="#4CAF50"
                        )
                        page.update()
                        
                        # Redirigir al dashboard
                        from modules import dashboard
                        dashboard.dashboard_view(container, page=page)
                    else:
                        mensaje.value = "❌ Contraseña incorrecta"
                        print(f"❌ Contraseña incorrecta para: {usuario.value}")
                        page.update()
                else:
                    mensaje.value = "❌ Usuario no encontrado o inactivo"
                    print(f"❌ Usuario no encontrado: {usuario.value}")
                    page.update()
                    
        except Exception as err:
            mensaje.value = f"❌ Error del sistema: {err}"
            print(f"❌ Error #{contador_intentos['valor']}: {err}")
            import traceback
            traceback.print_exc()
            page.update()

    def on_enter_pressed(e):
        """Permite login con Enter"""
        autenticar(e)

    usuario.on_submit = on_enter_pressed
    password.on_submit = on_enter_pressed

    btn_login = ft.ElevatedButton(
        text="Iniciar Sesión", 
        icon=ft.icons.LOGIN,
        on_click=autenticar,
        style=ft.ButtonStyle(
            bgcolor="#2E7D32",
            color="white",
            padding=15
        ),
        width=300
    )

    # Logo/Título
    logo = ft.Container(
        content=ft.Column([
            ft.Icon(ft.icons.NATURE, size=60, color="#2E7D32"),
            ft.Text("Vivero Rocío", size=32, weight="bold", color="#2E7D32"),
            ft.Text("Sistema de Gestión", size=14, color="#666"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
        margin=ft.margin.only(bottom=30)
    )

    # Card de login
    login_card = ft.Container(
        content=ft.Column(
            [
                logo,
                usuario,
                password,
                mensaje,
                btn_login,
                ft.Container(height=10),
                ft.Text("Usuario: admin | Contraseña: admin123", size=11, color="#999", italic=True)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        ),
        padding=40,
        bgcolor="white",
        border_radius=15,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.colors.with_opacity(0.1, "black"),
        )
    )

    container.controls.clear()
    container.controls.append(
        ft.Container(
            content=login_card,
            alignment=ft.alignment.center,
            expand=True,
            bgcolor="#f5f5f5"
        )
    )
    page.update()
    print("✅ Login view con mejor contraste renderizado")
