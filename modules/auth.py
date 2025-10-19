import flet as ft
import sqlite3
import hashlib
from datetime import datetime, timedelta
import time

# Importar el gestor de sesión
try:
    from session_manager import session
except ImportError:
    class BasicSession:
        def __init__(self):
            self.current_user = None
        def login(self, user_data):
            self.current_user = user_data
            return True
        def logout(self):
            self.current_user = None
        def is_logged_in(self):
            return self.current_user is not None
        def get_current_user(self):
            return self.current_user
    session = BasicSession()

DB = "data/vivero.db"
PRIMARY_COLOR = "#2E7D32"
ACCENT_COLOR = "#66BB6A"
SUCCESS_COLOR = "#4CAF50"
WARNING_COLOR = "#FF9800"
ERROR_COLOR = "#F44336"

def login_view(content, page=None, navigate=None):
    print(f"🎨 Iniciando login view innovador...")
    page.window_maximized = True  # 🔹 Forzar inicio maximizado
    
    # Limpiar contenido
    content.controls.clear()

    # --- Variables de estado ---
    login_attempts = 0
    max_attempts = 3
    current_time = datetime.now()

    # --- Campos del formulario con mejor contraste ---
    username = ft.TextField(
        label="Usuario",
        width=400,
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        border_radius=15,
        hint_text="Buscar usuario...",
        autofocus=True,
        bgcolor=ft.Colors.WHITE,
        color=ft.Colors.BLACK,
        border_color=ft.Colors.GREY_400,
        focused_border_color=PRIMARY_COLOR,
        cursor_color=PRIMARY_COLOR,
        text_size=16,
        label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=14),
        hint_style=ft.TextStyle(color=ft.Colors.GREY_500),
    )
    
    password = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        width=400,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        border_radius=15,
        hint_text="Ingresa tu contraseña segura",
        bgcolor=ft.Colors.WHITE,
        color=ft.Colors.BLACK,
        border_color=ft.Colors.GREY_400,
        focused_border_color=PRIMARY_COLOR,
        cursor_color=PRIMARY_COLOR,
        text_size=16,
        label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=14),
        hint_style=ft.TextStyle(color=ft.Colors.GREY_500),
    )
    
    # --- Indicadores visuales con mejor contraste ---
    status_container = ft.Container(
        content=ft.Text("", size=14, text_align=ft.TextAlign.CENTER, weight="bold"),
        padding=ft.padding.symmetric(vertical=10, horizontal=16),
        border_radius=12,
        bgcolor=ft.Colors.TRANSPARENT,
        visible=False,
    )
    
    loading_indicator = ft.Container(
        content=ft.Row([
            ft.ProgressRing(width=24, height=24, stroke_width=3, color=PRIMARY_COLOR),
            ft.Text("Verificando credenciales...", size=14, color=PRIMARY_COLOR, weight="bold"),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
        visible=False,
        padding=10,
        border_radius=10,
        bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
    )

    # --- Container para sugerencias con mejor visibilidad ---
    suggestions_list = ft.Column([], spacing=2)
    suggestions_container = ft.Container(
        content=ft.ListView(
            controls=[suggestions_list],
            height=180,
        ),
        visible=False,
        width=400,
        border_radius=15,
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(2, PRIMARY_COLOR),
        padding=ft.padding.symmetric(vertical=8),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            offset=ft.Offset(0, 5),
        ),
    )

    # --- Panel de últimos accesos mejorado ---
    recent_logins_list = ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.HISTORY, color=PRIMARY_COLOR, size=22),
            ft.Text("Últimos Accesos", size=16, weight="bold", color=PRIMARY_COLOR),
        ], spacing=8),
        ft.Divider(height=2, color=PRIMARY_COLOR, opacity=0.3),
    ], spacing=10)
    
    recent_logins_container = ft.Container(
        content=recent_logins_list,
        width=400,
        padding=20,
        border_radius=15,
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(1, PRIMARY_COLOR),
        visible=False,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            offset=ft.Offset(0, 3),
        ),
    )

    # --- Funciones (mantener las mismas funciones anteriores) ---
    def obtener_usuarios_con_detalles():
        """Obtiene usuarios con información detallada"""
        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("""
                SELECT username, nombre_completo, rol, ultimo_acceso, 
                       CASE 
                           WHEN ultimo_acceso IS NULL THEN 'Nunca'
                           ELSE datetime(ultimo_acceso, 'localtime')
                       END as ultimo_acceso_formatted
                FROM usuarios 
                WHERE estado = 'Activo' 
                ORDER BY 
                    CASE WHEN ultimo_acceso IS NULL THEN 1 ELSE 0 END,
                    ultimo_acceso DESC
            """)
            usuarios = cur.fetchall()
            conn.close()
            return usuarios
        except Exception as e:
            print(f"Error obteniendo usuarios: {e}")
            return [
                ('admin', 'Administrador del Sistema', 'Administrador', None, 'Nunca'),
                ('gerente', 'María Gerente', 'Gerente', None, 'Nunca'),
                ('vendedor', 'Juan Vendedor', 'Vendedor', None, 'Nunca'),
                ('usuario', 'Carlos Usuario', 'Usuario', None, 'Nunca'),
            ]

    def obtener_ultimos_accesos():
        """Obtiene los últimos 5 accesos al sistema"""
        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("""
                SELECT u.username, u.nombre_completo, u.rol, u.ultimo_acceso,
                       datetime(u.ultimo_acceso, 'localtime') as acceso_formateado
                FROM usuarios u
                WHERE u.ultimo_acceso IS NOT NULL AND u.estado = 'Activo'
                ORDER BY u.ultimo_acceso DESC
                LIMIT 5
            """)
            accesos = cur.fetchall()
            conn.close()
            return accesos
        except Exception as e:
            print(f"Error obteniendo últimos accesos: {e}")
            return []

    def filtrar_usuarios_inteligente(texto):
        """Filtrado inteligente de usuarios"""
        if not texto or len(texto) < 1:
            return []
        
        todos_usuarios = obtener_usuarios_con_detalles()
        texto_lower = texto.lower()
        
        exactos = []
        que_empiezan = []
        que_contienen = []
        
        for user in todos_usuarios:
            username_u, nombre, rol, _, _ = user
            if username_u.lower() == texto_lower:
                exactos.append(user)
            elif username_u.lower().startswith(texto_lower) or nombre.lower().startswith(texto_lower):
                que_empiezan.append(user)
            elif texto_lower in username_u.lower() or texto_lower in nombre.lower():
                que_contienen.append(user)
        
        resultado = exactos + que_empiezan + que_contienen
        return resultado[:5]

    def crear_sugerencia_avanzada(usuario_info):
        """Crea sugerencia de usuario con información rica y mejor contraste"""
        username_sugerido, nombre_completo, rol, ultimo_acceso, ultimo_acceso_formatted = usuario_info
        
        # Colores más contrastantes por rol
        rol_colors = {
            "Administrador": "#C62828",  # Rojo más oscuro
            "Gerente": "#1565C0",        # Azul más oscuro
            "Vendedor": "#2E7D32",       # Verde oscuro
            "Usuario": "#424242"         # Gris oscuro
        }
        
        def seleccionar_usuario(e):
            username.value = username_sugerido
            password.focus()
            ocultar_sugerencias()
            mostrar_info_usuario(username_sugerido, nombre_completo, rol, ultimo_acceso_formatted)
            page.update()
        
        suggestion_item = ft.Container(
            content=ft.Row([
                # Avatar con mejor contraste
                ft.Container(
                    content=ft.Text(username_sugerido[0].upper(), color="white", weight="bold", size=16),
                    width=45,
                    height=45,
                    border_radius=22.5,
                    bgcolor=rol_colors.get(rol, "#424242"),
                    alignment=ft.alignment.center,
                    border=ft.border.all(2, ft.Colors.WHITE),
                ),
                # Info con mejor legibilidad
                ft.Column([
                    ft.Row([
                        ft.Text(username_sugerido, weight="bold", size=15, color=ft.Colors.BLACK),
                        ft.Container(
                            content=ft.Text(rol, size=10, color="white", weight="bold"),
                            bgcolor=rol_colors.get(rol, "#424242"),
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            border_radius=10,
                        ),
                    ], spacing=8),
                    ft.Text(nombre_completo, size=12, color=ft.Colors.GREY_700),
                    ft.Text(f"Último: {ultimo_acceso_formatted}", size=10, color=ft.Colors.GREY_600),
                ], spacing=3, expand=True),
                ft.Icon(ft.Icons.LOGIN, color=PRIMARY_COLOR, size=20),
            ], spacing=12),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            on_click=seleccionar_usuario,
            bgcolor=ft.Colors.TRANSPARENT,
            border_radius=12,
            ink=True,
        )
        
        def on_hover(e):
            if e.data == "true":
                suggestion_item.bgcolor = ft.Colors.with_opacity(0.1, PRIMARY_COLOR)
            else:
                suggestion_item.bgcolor = ft.Colors.TRANSPARENT
            page.update()
        
        suggestion_item.on_hover = on_hover
        return suggestion_item

    def mostrar_sugerencias():
        """Muestra sugerencias"""
        filtrados = filtrar_usuarios_inteligente(username.value)
        suggestions_list.controls.clear()
        
        if filtrados:
            for usuario in filtrados:
                suggestions_list.controls.append(crear_sugerencia_avanzada(usuario))
            suggestions_container.visible = True
        else:
            suggestions_container.visible = False
        
        page.update()

    def ocultar_sugerencias():
        """Oculta sugerencias"""
        suggestions_container.visible = False
        page.update()

    def mostrar_info_usuario(user, nombre, rol, ultimo_acceso):
        """Muestra información del usuario seleccionado"""
        info_text = f"👤 {nombre} | 🎭 {rol}"
        if ultimo_acceso != 'Nunca':
            info_text += f" | 🕒 {ultimo_acceso}"
        
        status_container.content = ft.Text(info_text, size=12, color=PRIMARY_COLOR, weight="bold")
        status_container.bgcolor = ft.Colors.with_opacity(0.15, PRIMARY_COLOR)
        status_container.visible = True
        page.update()

    def mostrar_ultimos_accesos():
        """Muestra panel de últimos accesos"""
        accesos = obtener_ultimos_accesos()
        
        # Limpiar lista existente
        recent_logins_list.controls.clear()
        
        # Header con mejor contraste
        recent_logins_list.controls.extend([
            ft.Row([
                ft.Icon(ft.Icons.HISTORY, color=PRIMARY_COLOR, size=22),
                ft.Text("Últimos Accesos", size=16, weight="bold", color=PRIMARY_COLOR),
            ], spacing=8),
            ft.Divider(height=2, color=PRIMARY_COLOR, opacity=0.3),
        ])
        
        if accesos:
            for acceso in accesos:
                username_acc, nombre_acc, rol_acc, _, acceso_formatted = acceso
                
                try:
                    acceso_dt = datetime.strptime(acceso_formatted, '%Y-%m-%d %H:%M:%S')
                    tiempo_transcurrido = datetime.now() - acceso_dt
                    
                    if tiempo_transcurrido < timedelta(minutes=1):
                        tiempo_str = "Hace un momento"
                        tiempo_color = ft.Colors.GREEN_700
                    elif tiempo_transcurrido < timedelta(hours=1):
                        minutos = int(tiempo_transcurrido.total_seconds() / 60)
                        tiempo_str = f"Hace {minutos} min"
                        tiempo_color = ft.Colors.GREEN_700
                    elif tiempo_transcurrido < timedelta(days=1):
                        horas = int(tiempo_transcurrido.total_seconds() / 3600)
                        tiempo_str = f"Hace {horas}h"
                        tiempo_color = ft.Colors.ORANGE_700
                    else:
                        dias = tiempo_transcurrido.days
                        tiempo_str = f"Hace {dias}d"
                        tiempo_color = ft.Colors.GREY_700
                except:
                    tiempo_str = acceso_formatted
                    tiempo_color = ft.Colors.GREY_700
                
                acceso_item = ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(username_acc[0].upper(), color="white", weight="bold", size=12),
                            width=32,
                            height=32,
                            border_radius=16,
                            bgcolor=PRIMARY_COLOR,
                            alignment=ft.alignment.center,
                        ),
                        ft.Column([
                            ft.Text(f"{username_acc} ({nombre_acc})", size=12, weight="bold", color=ft.Colors.BLACK),
                            ft.Text(f"{rol_acc} • {tiempo_str}", size=10, color=tiempo_color, weight="bold"),
                        ], spacing=2, expand=True),
                    ], spacing=10),
                    padding=ft.padding.symmetric(vertical=6, horizontal=10),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.05, PRIMARY_COLOR),
                    border=ft.border.all(1, ft.Colors.with_opacity(0.2, PRIMARY_COLOR)),
                )
                
                recent_logins_list.controls.append(acceso_item)
        else:
            recent_logins_list.controls.append(
                ft.Text("No hay accesos recientes", size=12, color=ft.Colors.GREY_600, weight="bold")
            )
        
        recent_logins_container.visible = True
        page.update()

    def on_username_change(e):
        """Maneja cambios en el campo usuario"""
        if username.value and len(username.value) >= 1:
            mostrar_sugerencias()
            status_container.visible = False
        else:
            ocultar_sugerencias()
            status_container.visible = False
        page.update()

    def validar_credenciales(user, pass_text):
        """Validación de credenciales"""
        if not user or not pass_text:
            return None, "⚠️ Por favor, completa todos los campos"
        
        try:
            password_hash = hashlib.sha256(pass_text.encode()).hexdigest()
            
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, username, nombre_completo, rol, estado, ultimo_acceso
                FROM usuarios 
                WHERE username=? AND password=?
            """, (user, password_hash))
            
            usuario = cur.fetchone()
            conn.close()
            
            if not usuario:
                return None, "❌ Credenciales incorrectas"
            
            user_id, username_db, nombre_completo, rol, estado, ultimo_acceso = usuario
            
            if estado != 'Activo':
                return None, f"🚫 Usuario '{username_db}' deshabilitado"
            
            return {
                'id': user_id,
                'username': username_db,
                'nombre_completo': nombre_completo,
                'rol': rol,
                'ultimo_acceso': ultimo_acceso
            }, None
            
        except Exception as e:
            return None, f"❌ Error del sistema: {str(e)}"

    def actualizar_ultimo_acceso(user_id):
        """Actualiza último acceso"""
        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(
                "UPDATE usuarios SET ultimo_acceso = datetime('now', 'localtime') WHERE id = ?",
                (user_id,)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error actualizando último acceso: {e}")

    def mostrar_status(mensaje, tipo="info"):
        """Muestra mensajes de estado con mejor contraste"""
        colores = {
            "success": (ft.Colors.WHITE, SUCCESS_COLOR),
            "error": (ft.Colors.WHITE, ERROR_COLOR),
            "warning": (ft.Colors.WHITE, WARNING_COLOR),
            "info": (ft.Colors.WHITE, PRIMARY_COLOR)
        }
        
        color_texto, color_fondo = colores.get(tipo, colores["info"])
        
        status_container.content = ft.Text(mensaje, size=14, color=color_texto, weight="bold")
        status_container.bgcolor = color_fondo
        status_container.visible = True
        page.update()

    def mostrar_loading(mostrar=True):
        """Control de loading"""
        loading_indicator.visible = mostrar
        login_button.disabled = mostrar
        if mostrar:
            ocultar_sugerencias()
        page.update()

    def do_login(e=None):
        """Proceso de login"""
        nonlocal login_attempts
        
        print(f"🔐 Intento de login #{login_attempts + 1}: {username.value}")
        
        if login_attempts >= max_attempts:
            mostrar_status("🚫 Demasiados intentos. Espera un momento...", "error")
            return
        
        ocultar_sugerencias()
        status_container.visible = False
        mostrar_loading(True)
        
        # Validar credenciales
        usuario, error = validar_credenciales(username.value.strip(), password.value)
        
        if error:
            login_attempts += 1
            print(f"❌ Error #{login_attempts}: {error}")
            
            mostrar_loading(False)
            mostrar_status(error, "error")
            
            if "incorrectas" in error:
                password.value = ""
                password.focus()
                username.border_color = ERROR_COLOR
                password.border_color = ERROR_COLOR
                page.update()
            
            return
        
        # Login exitoso
        login_attempts = 0
        print(f"✅ Login exitoso: {usuario['username']} ({usuario['rol']})")
        
        actualizar_ultimo_acceso(usuario['id'])
        session.login(usuario)
        
        username.border_color = SUCCESS_COLOR
        password.border_color = SUCCESS_COLOR
        mostrar_status(f"¡Bienvenido, {usuario['nombre_completo']}! 🎉", "success")
        mostrar_loading(False)
        
        username.value = ""
        password.value = ""
        
        # Navegar con delay
        def navigate_delayed():
            time.sleep(1.5)
            try:
                from modules import dashboard
                print("🚀 Navegando al dashboard...")
                dashboard.dashboard_view(content, page=page)
            except Exception as nav_error:
                print(f"❌ Error navegación: {nav_error}")
                mostrar_status(f"Error: {str(nav_error)}", "error")
        
        import threading
        threading.Thread(target=navigate_delayed, daemon=True).start()

    # --- Eventos ---
    username.on_change = on_username_change
    username.on_submit = do_login
    password.on_submit = do_login
    
    def on_page_click(e):
        if suggestions_container.visible:
            ocultar_sugerencias()

    # --- Botón principal con mejor contraste ---
    login_button = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.LOGIN, size=20, color="white"),
            ft.Text("Iniciar Sesión", size=16, weight="bold", color="white"),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        width=400,
        height=55,
        bgcolor=PRIMARY_COLOR,
        color="white",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=15),
            elevation={"": 3, "hovered": 6},
            shadow_color=PRIMARY_COLOR,
        ),
        on_click=do_login,
    )

    # --- Botones de ayuda con mejor visibilidad ---
    def mostrar_usuarios_disponibles():
        """Modal con usuarios disponibles"""
        usuarios_text = """👥 Usuarios de prueba disponibles:

🔑 ADMINISTRADOR:
   Usuario: admin
   Contraseña: admin123

🏢 GERENTE:
   Usuario: gerente
   Contraseña: gerente123

💼 VENDEDOR:
   Usuario: vendedor
   Contraseña: vendedor123

👤 USUARIO BÁSICO:
   Usuario: usuario
   Contraseña: usuario123

🚫 INACTIVO (no puede ingresar):
   Usuario: inactivo
   Contraseña: inactivo123"""
        
        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Usuarios del Sistema", weight="bold", color=PRIMARY_COLOR, size=18),
            content=ft.Text(usuarios_text, size=14),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update())
            ],
        )
        page.dialog.open = True
        page.update()

    help_buttons = ft.Row([
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=16, color=PRIMARY_COLOR),
                ft.Text("Usuarios", size=12, color=PRIMARY_COLOR, weight="bold"),
            ], spacing=4),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, PRIMARY_COLOR),
            ink=True,
            on_click=lambda e: mostrar_usuarios_disponibles(),
        ),
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.HISTORY, size=16, color=ACCENT_COLOR),
                ft.Text("Últimos Accesos", size=12, color=ACCENT_COLOR, weight="bold"),
            ], spacing=4),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ACCENT_COLOR),
            ink=True,
            on_click=lambda e: mostrar_ultimos_accesos(),
        ),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # --- Header con MUCHO mejor contraste ---
    header_container = ft.Container(
        content=ft.Column([
            # Icono con fondo contrastante
            ft.Container(
                content=ft.Icon(ft.Icons.SPA, size=80, color=PRIMARY_COLOR),
                width=120,
                height=120,
                border_radius=60,
                bgcolor=ft.Colors.WHITE,
                alignment=ft.alignment.center,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                    offset=ft.Offset(0, 5),
                ),
            ),
            
            # Título con sombra de texto
            ft.Container(
                content=ft.Text("🌱 Vivero Rocío", size=42, weight="bold", color="white"),
                padding=ft.padding.symmetric(horizontal=20, vertical=8),
                border_radius=15,
                bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
            ),
            
            # Subtítulo con fondo
            ft.Container(
                content=ft.Text("Sistema de Gestión Avanzado", size=18, color="white", weight="bold"),
                padding=ft.padding.symmetric(horizontal=16, vertical=6),
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            ),
            
            # Fecha/hora con mejor contraste
            ft.Container(
                content=ft.Text(
                    f"📅 {current_time.strftime('%d/%m/%Y')} • ⏰ {current_time.strftime('%H:%M')}", 
                    size=13, 
                    color=PRIMARY_COLOR,
                    weight="bold"
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=12,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, PRIMARY_COLOR),
            ),
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
    )

    # --- Formulario principal con mejor contraste ---
    login_form = ft.Container(
        content=ft.Column([
            header_container,
            ft.Container(height=20),
            username,
            suggestions_container,
            password,
            status_container,
            loading_indicator,
            ft.Container(height=15),
            login_button,
            ft.Container(height=20),
            help_buttons,
            ft.Container(height=20),
            recent_logins_container,
        ], 
        spacing=12,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER),
        
        width=480,
        padding=30,
        border_radius=25,
        bgcolor=ft.Colors.with_opacity(0.98, ft.Colors.WHITE),
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=25,
            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            offset=ft.Offset(0, 10),
        ),
    )

    # --- Fondo con gradiente más suave ---
    background = ft.Container(
        content=ft.Container(
            content=login_form,
            alignment=ft.alignment.center,
            expand=True,
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[
                "#388E3C",  # Verde más oscuro
                PRIMARY_COLOR,
                ACCENT_COLOR,
            ],
        ),
        expand=True,
    )

    content.controls.append(background)
    page.on_click = on_page_click
    
    print("✅ Login view con mejor contraste renderizado")
    page.update()