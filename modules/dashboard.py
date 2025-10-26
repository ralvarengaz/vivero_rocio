"""
Módulo Dashboard
Migrado a nueva arquitectura con PostgreSQL, Config y Utils
"""
import flet as ft
from modules.db_service import db
from modules.config import Colors, FontSizes, Sizes, Messages, Icons, Spacing
from modules.utils import format_guarani
from modules.session_service import session
from modules import productos, clientes, proveedores, pedidos, ventas, reportes, usuarios


def obtener_kpis():
    """Obtiene los KPIs del dashboard desde PostgreSQL"""
    kpis = {
        "ventas_totales": 0,
        "pedidos_pendientes": 0,
        "pedidos_entregados": 0,
        "clientes_totales": 0
    }

    try:
        with db.get_connection() as conn:
            cur = conn.cursor()

            # Ventas totales
            cur.execute("SELECT COALESCE(SUM(total), 0) FROM ventas")
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

    return kpis


def obtener_ventas_recientes():
    """Obtiene las ventas más recientes desde PostgreSQL"""
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT v.id, c.nombre, v.total, v.fecha_venta
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                ORDER BY v.fecha_venta DESC LIMIT 6
            """)
            ventas = cur.fetchall()
            return ventas
    except Exception as e:
        print(f"Error obteniendo ventas recientes: {e}")
        return []


def obtener_pedidos_recientes():
    """Obtiene los pedidos más recientes desde PostgreSQL"""
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT p.id, c.nombre, p.destino, p.estado, p.fecha_pedido
                FROM pedidos p
                LEFT JOIN clientes c ON p.cliente_id = c.id
                ORDER BY p.fecha_pedido DESC LIMIT 6
            """)
            pedidos_rows = cur.fetchall()
            return pedidos_rows
    except Exception as e:
        print(f"Error obteniendo pedidos recientes: {e}")
        return []


def dashboard_view(content, page=None):
    """Vista principal del dashboard"""
    # Limpiar contenido según el tipo de contenedor
    if hasattr(content, 'controls'):
        content.controls.clear()
    else:
        content.content = None

    # Verificar sesión activa
    if not session.is_logged_in():
        from modules import auth
        auth.login_view(content, page)
        return

    current_user = session.get_current_user()
    modulos_permitidos = session.get_modulos_permitidos()

    # Funciones de navegación
    def go_to(view_func, modulo_name):
        def handler(e):
            if session.tiene_permiso(modulo_name, 'ver'):
                view_func(content, page=page)
            else:
                page.open(ft.SnackBar(
                    content=ft.Text(f"🚫 No tienes permisos para acceder a {modulo_name.capitalize()}", color=Colors.TEXT_WHITE),
                    bgcolor=Colors.ERROR,
                    duration=3000
                ))
        return handler

    def crear_menu_item(titulo, icono, modulo, view_func):
        """Crea un item del menú si el usuario tiene permisos"""
        if modulo not in modulos_permitidos:
            return None

        color = Colors.TEXT_WHITE
        try:
            permisos = current_user.get('permisos', {}).get(modulo, {})
            if not permisos.get('crear', False) and not permisos.get('editar', False):
                color = "#FFE0B2"
        except:
            pass

        return ft.ListTile(
            title=ft.Text(titulo, color=color),
            leading=ft.Icon(icono, color=color),
            on_click=go_to(view_func, modulo),
        )

    # Crear items del menú con permisos
    menu_items = []

    items_config = [
        ("Productos", ft.icons.SPA, "productos", productos.crud_view),
        ("Clientes", ft.icons.PEOPLE, "clientes", clientes.crud_view),
        ("Proveedores", ft.icons.LOCAL_SHIPPING, "proveedores", proveedores.crud_view),
        ("Pedidos", ft.icons.RECEIPT, "pedidos", pedidos.crud_view),
        ("Ventas", ft.icons.PAID, "ventas", ventas.crud_view),
        ("Reportes", ft.icons.INSERT_CHART, "reportes", reportes.crud_view),
        ("Usuarios", ft.icons.ADMIN_PANEL_SETTINGS, "usuarios", usuarios.crud_view),
    ]

    for titulo, icono, modulo, view_func in items_config:
        item = crear_menu_item(titulo, icono, modulo, view_func)
        if item:
            menu_items.append(item)

    if not menu_items:
        menu_items.append(
            ft.ListTile(
                title=ft.Text("Sin acceso", color=Colors.ERROR),
                leading=ft.Icon(ft.icons.BLOCK, color=Colors.ERROR),
            )
        )

    # Botón de cerrar sesión
    def cerrar_sesion(e):
        session.logout()
        from modules import auth
        auth.login_view(content, page)

    logout_button = ft.ListTile(
        title=ft.Text("Cerrar Sesión", color=Colors.ERROR),
        leading=ft.Icon(ft.icons.LOGOUT, color=Colors.ERROR),
        on_click=cerrar_sesion,
    )

    # Sidebar
    sidebar = ft.Container(
        content=ft.Column([
            # Header del usuario
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text(current_user['username'][0].upper(), size=FontSizes.LARGE, weight="bold"),
                            color=Colors.TEXT_WHITE,
                            bgcolor=Colors.PRIMARY,
                            radius=20,
                        ),
                        ft.Column([
                            ft.Text("🌱 Vivero Rocío", size=FontSizes.NORMAL, weight="bold", color=Colors.TEXT_WHITE),
                            ft.Text(f"{current_user['nombre_completo']}", size=FontSizes.SMALL, color=Colors.TEXT_WHITE, opacity=0.9),
                            ft.Text(f"👤 {current_user['rol']}", size=FontSizes.XSMALL, color=Colors.ACCENT, weight="bold"),
                        ], spacing=Spacing.XSMALL),
                    ], spacing=Spacing.NORMAL, alignment=ft.MainAxisAlignment.START),
                ], spacing=Spacing.SMALL),
                padding=ft.padding.only(bottom=Spacing.MEDIUM),
            ),
            ft.Divider(color=Colors.TEXT_WHITE, opacity=0.3),

            # Items del menú
            *menu_items,

            ft.Divider(color=Colors.TEXT_WHITE, opacity=0.3),
            logout_button,
        ], spacing=Spacing.SMALL, expand=True),
        width=220,
        padding=Spacing.LARGE,
        bgcolor=Colors.SIDEBAR_BG,
        border_radius=ft.border_radius.only(top_left=0, bottom_left=0, top_right=20, bottom_right=20),
        shadow=ft.BoxShadow(blur_radius=15, color="#444"),
    )

    # KPIs Cards
    kpis = obtener_kpis()
    kpi_cards = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.PAID, color=Colors.INFO, size=32),
                ft.Text("Ventas Totales", size=FontSizes.NORMAL, text_align=ft.TextAlign.CENTER),
                ft.Text(format_guarani(kpis['ventas_totales']), size=FontSizes.XLARGE, weight="bold"),
            ], spacing=Spacing.SMALL, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#E3F2FD",
            padding=Spacing.LARGE,
            border_radius=Sizes.CARD_RADIUS,
            width=180,
            shadow=ft.BoxShadow(blur_radius=12, color=Colors.INFO),
        ),
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.RECEIPT, color=Colors.WARNING, size=32),
                ft.Text("Pedidos Pendientes", size=FontSizes.NORMAL, text_align=ft.TextAlign.CENTER),
                ft.Text(f"{kpis['pedidos_pendientes']}", size=FontSizes.XLARGE, weight="bold"),
            ], spacing=Spacing.SMALL, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#FFF3E0",
            padding=Spacing.LARGE,
            border_radius=Sizes.CARD_RADIUS,
            width=180,
            shadow=ft.BoxShadow(blur_radius=12, color=Colors.WARNING),
        ),
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.DONE, color=Colors.SUCCESS, size=32),
                ft.Text("Pedidos Entregados", size=FontSizes.NORMAL, text_align=ft.TextAlign.CENTER),
                ft.Text(f"{kpis['pedidos_entregados']}", size=FontSizes.XLARGE, weight="bold"),
            ], spacing=Spacing.SMALL, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#E8F5E9",
            padding=Spacing.LARGE,
            border_radius=Sizes.CARD_RADIUS,
            width=180,
            shadow=ft.BoxShadow(blur_radius=12, color=Colors.SUCCESS),
        ),
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.PEOPLE, color="#0288D1", size=32),
                ft.Text("Clientes Totales", size=FontSizes.NORMAL, text_align=ft.TextAlign.CENTER),
                ft.Text(f"{kpis['clientes_totales']}", size=FontSizes.XLARGE, weight="bold"),
            ], spacing=Spacing.SMALL, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#E3F2FD",
            padding=Spacing.LARGE,
            border_radius=Sizes.CARD_RADIUS,
            width=180,
            shadow=ft.BoxShadow(blur_radius=12, color="#0288D1"),
        ),
    ], spacing=Spacing.XLARGE, alignment=ft.MainAxisAlignment.START)

    # Tabla de ventas recientes
    ventas_recientes = obtener_ventas_recientes()
    ventas_tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", color=Colors.PRIMARY)),
            ft.DataColumn(ft.Text("Cliente", color=Colors.PRIMARY)),
            ft.DataColumn(ft.Text("Monto", color=Colors.PRIMARY)),
            ft.DataColumn(ft.Text("Fecha", color=Colors.PRIMARY)),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(v[0]))),
                ft.DataCell(ft.Text(v[1] or "Sin cliente")),
                ft.DataCell(ft.Text(format_guarani(v[2]))),
                ft.DataCell(ft.Text(str(v[3])[:19] if v[3] else "")),
            ]) for v in ventas_recientes
        ],
        column_spacing=8,
    )

    ventas_card = ft.Container(
        content=ft.Column([
            ft.Text("Ventas Recientes", weight="bold", size=FontSizes.LARGE, color=Colors.PRIMARY),
            ft.ListView([ft.Row([ventas_tabla], scroll=ft.ScrollMode.AUTO)], expand=True, height=220)
        ], spacing=Spacing.NORMAL),
        bgcolor=Colors.CARD_BG,
        border_radius=Sizes.CARD_RADIUS,
        padding=Spacing.LARGE,
        expand=True,
        shadow=ft.BoxShadow(blur_radius=10, color="#BBB"),
    )

    # Tabla de pedidos recientes
    pedidos_recientes = obtener_pedidos_recientes()
    pedidos_tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", color=Colors.PRIMARY)),
            ft.DataColumn(ft.Text("Cliente", color=Colors.PRIMARY)),
            ft.DataColumn(ft.Text("Destino", color=Colors.PRIMARY)),
            ft.DataColumn(ft.Text("Estado", color=Colors.PRIMARY)),
            ft.DataColumn(ft.Text("Fecha", color=Colors.PRIMARY)),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(p[0]))),
                ft.DataCell(ft.Text(p[1] or "Sin cliente")),
                ft.DataCell(ft.Text(p[2] or "")),
                ft.DataCell(ft.Text(p[3])),
                ft.DataCell(ft.Text(str(p[4])[:19] if p[4] else "")),
            ]) for p in pedidos_recientes
        ],
        column_spacing=8,
    )

    pedidos_card = ft.Container(
        content=ft.Column([
            ft.Text("Pedidos Recientes", weight="bold", size=FontSizes.LARGE, color=Colors.PRIMARY),
            ft.ListView([ft.Row([pedidos_tabla], scroll=ft.ScrollMode.AUTO)], expand=True, height=220)
        ], spacing=Spacing.NORMAL),
        bgcolor=Colors.CARD_BG,
        border_radius=Sizes.CARD_RADIUS,
        padding=Spacing.LARGE,
        expand=True,
        shadow=ft.BoxShadow(blur_radius=10, color="#BBB"),
    )

    # Información de permisos del usuario
    permisos_info = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.VERIFIED_USER, color=Colors.PRIMARY, size=20),
                ft.Text(f"Sesión: {current_user['nombre_completo']} ({current_user['rol']})",
                       size=FontSizes.NORMAL, weight="bold", color=Colors.PRIMARY),
            ], spacing=Spacing.SMALL),
            ft.Row([
                ft.Icon(ft.icons.DASHBOARD, color=Colors.INFO, size=16),
                ft.Text(f"Módulos disponibles: {len(modulos_permitidos)}", size=FontSizes.SMALL, color=Colors.INFO),
            ], spacing=Spacing.SMALL),
            ft.Row([
                ft.Icon(
                    ft.icons.ADMIN_PANEL_SETTINGS if current_user['rol'] == 'Administrador' else ft.icons.PERSON,
                    color=Colors.PRIMARY if current_user['rol'] == 'Administrador' else Colors.WARNING,
                    size=16
                ),
                ft.Text(
                    "🟢 Acceso completo" if current_user['rol'] == 'Administrador' else "🟡 Acceso limitado",
                    size=FontSizes.SMALL,
                    color=Colors.PRIMARY if current_user['rol'] == 'Administrador' else Colors.WARNING
                ),
            ], spacing=Spacing.SMALL),
        ], spacing=Spacing.SMALL),
        padding=Spacing.MEDIUM,
        border_radius=Spacing.NORMAL,
        bgcolor=ft.colors.with_opacity(0.1, Colors.PRIMARY),
        border=ft.border.all(1, Colors.PRIMARY),
    )

    # Layout principal
    main_panel = ft.Column([
        ft.Row([
            ft.Text(f"¡Bienvenido a Vivero Rocío!", size=FontSizes.XXLARGE, weight="bold", color=Colors.PRIMARY),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        permisos_info,
        ft.Divider(),
        kpi_cards,
        ft.Divider(),
        ft.Row([ventas_card, pedidos_card], spacing=Spacing.LARGE, expand=True),
    ], expand=True, spacing=Spacing.XLARGE, horizontal_alignment=ft.CrossAxisAlignment.START)

    # Agregar contenido según el tipo de contenedor
    dashboard_layout = ft.Row([
        sidebar,
        ft.Container(
            content=main_panel,
            padding=Sizes.CARD_PADDING,
            expand=True,
            bgcolor="#F4F8FB",
            border_radius=Sizes.CARD_RADIUS,
        ),
    ], expand=True)

    if hasattr(content, 'controls'):
        content.controls.append(dashboard_layout)
    else:
        content.content = dashboard_layout

    if page:
        page.update()

    print("✅ Dashboard cargado (PostgreSQL + Nueva Arquitectura)")
