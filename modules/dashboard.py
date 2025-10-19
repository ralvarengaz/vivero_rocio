import flet as ft
import sqlite3
from modules import productos, clientes, proveedores, pedidos, ventas, reportes, usuarios

# Importar el gestor de sesión
try:
    from session_manager import session
except ImportError:
    # Crear un gestor básico si no existe
    class BasicSession:
        def __init__(self):
            self.current_user = {'username': 'admin', 'rol': 'Administrador', 'nombre_completo': 'Administrador'}
        
        def is_logged_in(self):
            return True
        
        def get_current_user(self):
            return self.current_user
        
        def get_modulos_permitidos(self):
            return ['productos', 'clientes', 'proveedores', 'pedidos', 'ventas', 'reportes', 'usuarios']
        
        def tiene_permiso(self, modulo, accion='ver'):
            return True
    
    session = BasicSession()

PRIMARY_COLOR = "#2E7D32"
ACCENT_COLOR = "#66BB6A"
SIDEBAR_BG = "#1B2430"
CARD_BG = "#ffffff"
DB = "data/vivero.db"

def obtener_kpis():
    """Obtiene los KPIs del dashboard"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    kpis = {}
    
    try:
        # Ventas totales
        cur.execute("SELECT IFNULL(SUM(total), 0) FROM ventas")
        kpis["ventas_totales"] = cur.fetchone()[0]
        
        # Pedidos pendientes
        cur.execute("SELECT COUNT(*) FROM pedidos WHERE estado='Pendiente'")
        kpis["pedidos_pendientes"] = cur.fetchone()[0]
        
        # Pedidos entregados
        cur.execute("SELECT COUNT(*) FROM pedidos WHERE estado='Entregado'")
        kpis["pedidos_entregados"] = cur.fetchone()[0]
        
        # Clientes totales
        cur.execute("SELECT COUNT(*) FROM clientes")
        kpis["clientes_totales"] = cur.fetchone()[0]
        
    except Exception as e:
        print(f"Error obteniendo KPIs: {e}")
        # Valores por defecto si hay error
        kpis = {
            "ventas_totales": 0,
            "pedidos_pendientes": 0,
            "pedidos_entregados": 0,
            "clientes_totales": 0
        }
    finally:
        conn.close()
    
    return kpis

def obtener_ventas_recientes():
    """Obtiene las ventas más recientes"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT v.id, c.nombre, v.total, v.fecha_venta
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            ORDER BY v.fecha_venta DESC LIMIT 6
        """)
        ventas = cur.fetchall()
    except Exception as e:
        print(f"Error obteniendo ventas recientes: {e}")
        ventas = []
    finally:
        conn.close()
    
    return ventas

def obtener_pedidos_recientes():
    """Obtiene los pedidos más recientes"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT p.id, c.nombre, p.destino, p.estado, p.fecha_pedido
            FROM pedidos p
            LEFT JOIN clientes c ON p.cliente_id = c.id
            ORDER BY p.fecha_pedido DESC LIMIT 6
        """)
        pedidos_rows = cur.fetchall()
    except Exception as e:
        print(f"Error obteniendo pedidos recientes: {e}")
        pedidos_rows = []
    finally:
        conn.close()
    
    return pedidos_rows

def dashboard_view(content, page=None):
    # ⭐ CORRECCIÓN: Limpiar correctamente según el tipo de contenedor
    if hasattr(content, 'controls'):
        content.controls.clear()  # Para Column
    else:
        content.content = None  # Para Container

    # --- Verificar sesión activa ---
    if not session.is_logged_in():
        from modules import auth
        auth.login_view(content, page)
        return

    current_user = session.get_current_user()
    modulos_permitidos = session.get_modulos_permitidos()

    # --- Funciones de navegación ---
    def go_to(view_func, modulo_name):
        def handler(e):
            # Verificar permiso antes de navegar
            if session.tiene_permiso(modulo_name, 'ver'):
                view_func(content, page=page)
            else:
                page.open(ft.SnackBar(
                    content=ft.Text(f"🚫 No tienes permisos para acceder a {modulo_name.capitalize()}", color="white"),
                    bgcolor="#F44336",
                    duration=3000
                ))
        return handler

    def crear_menu_item(titulo, icono, modulo, view_func):
        """Crea un item del menú si el usuario tiene permisos"""
        if modulo not in modulos_permitidos:
            return None
        
        # Determinar color según permisos
        color = "white"
        try:
            permisos = current_user.get('permisos', {}).get(modulo, {})
            if not permisos.get('crear', False) and not permisos.get('editar', False):
                color = "#FFE0B2"  # Color más tenue para solo lectura
        except:
            pass
        
        return ft.ListTile(
            title=ft.Text(titulo, color=color),
            leading=ft.Icon(icono, color=color),
            on_click=go_to(view_func, modulo),
        )

    # Crear items del menú con permisos
    menu_items = []
    
    # Items del menú con verificación de permisos
    items_config = [
        ("Productos", ft.Icons.SPA, "productos", productos.crud_view),
        ("Clientes", ft.Icons.PEOPLE, "clientes", clientes.crud_view),
        ("Proveedores", ft.Icons.LOCAL_SHIPPING, "proveedores", proveedores.crud_view),
        ("Pedidos", ft.Icons.RECEIPT, "pedidos", pedidos.crud_view),
        ("Ventas", ft.Icons.PAID, "ventas", ventas.crud_view),
        ("Reportes", ft.Icons.INSERT_CHART, "reportes", reportes.crud_view),
        ("Usuarios", ft.Icons.ADMIN_PANEL_SETTINGS, "usuarios", usuarios.crud_view),
    ]
    
    for titulo, icono, modulo, view_func in items_config:
        item = crear_menu_item(titulo, icono, modulo, view_func)
        if item:
            menu_items.append(item)
    
    # Si no hay módulos permitidos
    if not menu_items:
        menu_items.append(
            ft.ListTile(
                title=ft.Text("Sin acceso", color="#FF5722"),
                leading=ft.Icon(ft.Icons.BLOCK, color="#FF5722"),
            )
        )

    # Botón de cerrar sesión
    def cerrar_sesion(e):
        session.logout()
        from modules import auth
        auth.login_view(content, page)

    logout_button = ft.ListTile(
        title=ft.Text("Cerrar Sesión", color="#FF5722"),
        leading=ft.Icon(ft.Icons.LOGOUT, color="#FF5722"),
        on_click=cerrar_sesion,
    )

    # --- Sidebar ---
    sidebar = ft.Container(
        content=ft.Column([
            # Header del usuario
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text(current_user['username'][0].upper(), size=20, weight="bold"),
                            color="white",
                            bgcolor=PRIMARY_COLOR,
                            radius=20,
                        ),
                        ft.Column([
                            ft.Text("🌱 Vivero Rocío", size=16, weight="bold", color="white"),
                            ft.Text(f"{current_user['nombre_completo']}", size=12, color="white", opacity=0.9),
                            ft.Text(f"👤 {current_user['rol']}", size=10, color=ACCENT_COLOR, weight="bold"),
                        ], spacing=2),
                    ], spacing=10, alignment=ft.MainAxisAlignment.START),
                ], spacing=5),
                padding=ft.padding.only(bottom=15),
            ),
            ft.Divider(color="white", opacity=0.3),
            
            # Items del menú
            *menu_items,
            
            ft.Divider(color="white", opacity=0.3),
            logout_button,
        ], spacing=8, expand=True),
        width=220,
        padding=20,
        bgcolor=SIDEBAR_BG,
        border_radius=ft.border_radius.only(top_left=0, bottom_left=0, top_right=20, bottom_right=20),
        shadow=ft.BoxShadow(blur_radius=15, color="#444"),
    )

    # --- KPIs Cards ---
    kpis = obtener_kpis()
    kpi_cards = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.PAID, color="#2196F3", size=32),
                ft.Text("Ventas Totales", size=16, text_align=ft.TextAlign.CENTER),
                ft.Text(f"₲ {kpis['ventas_totales']:,.0f}", size=24, weight="bold"),
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#E3F2FD",
            padding=20,
            border_radius=20,
            width=180,
            shadow=ft.BoxShadow(blur_radius=12, color="#2196F3"),
        ),
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.RECEIPT, color="#FF9800", size=32),
                ft.Text("Pedidos Pendientes", size=16, text_align=ft.TextAlign.CENTER),
                ft.Text(f"{kpis['pedidos_pendientes']}", size=24, weight="bold"),
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#FFF3E0",
            padding=20,
            border_radius=20,
            width=180,
            shadow=ft.BoxShadow(blur_radius=12, color="#FF9800"),
        ),
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.DONE, color="#4CAF50", size=32),
                ft.Text("Pedidos Entregados", size=16, text_align=ft.TextAlign.CENTER),
                ft.Text(f"{kpis['pedidos_entregados']}", size=24, weight="bold"),
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#E8F5E9",
            padding=20,
            border_radius=20,
            width=180,
            shadow=ft.BoxShadow(blur_radius=12, color="#4CAF50"),
        ),
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.PEOPLE, color="#0288D1", size=32),
                ft.Text("Clientes Totales", size=16, text_align=ft.TextAlign.CENTER),
                ft.Text(f"{kpis['clientes_totales']}", size=24, weight="bold"),
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#E3F2FD",
            padding=20,
            border_radius=20,
            width=180,
            shadow=ft.BoxShadow(blur_radius=12, color="#0288D1"),
        ),
    ], spacing=25, alignment=ft.MainAxisAlignment.START)

    # --- Tabla de ventas recientes ---
    ventas_recientes = obtener_ventas_recientes()
    ventas_tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Cliente", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Monto", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Fecha", color=PRIMARY_COLOR)),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(v[0]))),
                ft.DataCell(ft.Text(v[1] or "Sin cliente")),
                ft.DataCell(ft.Text(f"₲ {v[2]:,.0f}")),
                ft.DataCell(ft.Text(v[3])),
            ]) for v in ventas_recientes
        ],
        column_spacing=8,
    )

    ventas_card = ft.Container(
        content=ft.Column([
            ft.Text("Ventas Recientes", weight="bold", size=18, color=PRIMARY_COLOR),
            ft.ListView([ft.Row([ventas_tabla], scroll=ft.ScrollMode.AUTO)], expand=True, height=220)
        ], spacing=10),
        bgcolor=CARD_BG,
        border_radius=20,
        padding=20,
        expand=True,
        shadow=ft.BoxShadow(blur_radius=10, color="#BBB"),
    )

    # --- Tabla de pedidos recientes ---
    pedidos_recientes = obtener_pedidos_recientes()
    pedidos_tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Cliente", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Destino", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Estado", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Fecha", color=PRIMARY_COLOR)),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(p[0]))),
                ft.DataCell(ft.Text(p[1] or "Sin cliente")),
                ft.DataCell(ft.Text(p[2] or "")),
                ft.DataCell(ft.Text(p[3])),
                ft.DataCell(ft.Text(p[4])),
            ]) for p in pedidos_recientes
        ],
        column_spacing=8,
    )

    pedidos_card = ft.Container(
        content=ft.Column([
            ft.Text("Pedidos Recientes", weight="bold", size=18, color=PRIMARY_COLOR),
            ft.ListView([ft.Row([pedidos_tabla], scroll=ft.ScrollMode.AUTO)], expand=True, height=220)
        ], spacing=10),
        bgcolor=CARD_BG,
        border_radius=20,
        padding=20,
        expand=True,
        shadow=ft.BoxShadow(blur_radius=10, color="#BBB"),
    )

    # --- Información de permisos del usuario ---
    permisos_info = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.VERIFIED_USER, color=PRIMARY_COLOR, size=20),
                ft.Text(f"Sesión: {current_user['nombre_completo']} ({current_user['rol']})", 
                       size=16, weight="bold", color=PRIMARY_COLOR),
            ], spacing=8),
            ft.Row([
                ft.Icon(ft.Icons.DASHBOARD, color="#0288D1", size=16),
                ft.Text(f"Módulos disponibles: {len(modulos_permitidos)}", size=12, color="#0288D1"),
            ], spacing=5),
            ft.Row([
                ft.Icon(
                    ft.Icons.ADMIN_PANEL_SETTINGS if current_user['rol'] == 'Administrador' else ft.Icons.PERSON, 
                    color=PRIMARY_COLOR if current_user['rol'] == 'Administrador' else "#FF9800", 
                    size=16
                ),
                ft.Text(
                    "🟢 Acceso completo" if current_user['rol'] == 'Administrador' else "🟡 Acceso limitado", 
                    size=12, 
                    color=PRIMARY_COLOR if current_user['rol'] == 'Administrador' else "#FF9800"
                ),
            ], spacing=5),
        ], spacing=5),
        padding=15,
        border_radius=10,
        bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
        border=ft.border.all(1, PRIMARY_COLOR),
    )

    # --- Layout principal ---
    main_panel = ft.Column([
        ft.Row([
            ft.Text(f"¡Bienvenido a Vivero Rocío!", size=28, weight="bold", color=PRIMARY_COLOR),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        permisos_info,  # Información de permisos
        ft.Divider(),
        kpi_cards,
        ft.Divider(),
        ft.Row([ventas_card, pedidos_card], spacing=20, expand=True),
    ], expand=True, spacing=25, horizontal_alignment=ft.CrossAxisAlignment.START)

    # ⭐ CORRECCIÓN: Agregar contenido según el tipo de contenedor
    dashboard_layout = ft.Row([
        sidebar,
        ft.Container(
            content=main_panel,
            padding=30,
            expand=True,
            bgcolor="#F4F8FB",
            border_radius=20,
        ),
    ], expand=True)

    if hasattr(content, 'controls'):
        content.controls.append(dashboard_layout)
    else:
        content.content = dashboard_layout

    if page:
        page.update()