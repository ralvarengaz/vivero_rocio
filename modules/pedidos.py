import flet as ft
import webbrowser
import os
from datetime import date, datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from modules import dashboard
from modules.database_manager import get_db_connection

PRIMARY_COLOR = "#2E7D32"
ACCENT_COLOR = "#66BB6A"
SUCCESS_COLOR = "#4CAF50"
WARNING_COLOR = "#FF9800"
ERROR_COLOR = "#F44336"
BLUE_COLOR = "#2196F3"
TICKET_DIR = "tickets"

# ---------------- AUXILIARES ----------------
def parse_gs(valor: str) -> int:
    """Convierte texto de guaraníes a entero"""
    if not valor:
        return 0
    return int("".join(ch for ch in str(valor) if ch.isdigit()))

def format_gs(valor: int) -> str:
    """Formatea entero a guaraníes con separadores"""
    return f"Gs. {int(valor):,.0f}".replace(",", ".")

def obtener_productos():
    """Obtiene productos disponibles con stock - PostgreSQL"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, nombre,
                    COALESCE(precio_venta, precio_compra, precio, 0) as precio_final,
                    COALESCE(stock, 0) as stock_final
                FROM productos
                WHERE COALESCE(stock, 0) > 0
                ORDER BY nombre ASC
            """)
            productos = []
            for pid, nom, prec, stock in cur.fetchall():
                productos.append({
                    "id": pid,
                    "nombre": nom,
                    "precio": prec,
                    "stock": stock
                })
            return productos
    except Exception as e:
        print(f"❌ Error obteniendo productos: {e}")
        return []

def obtener_usuario_actual(page):
    """Obtiene el usuario actual de la sesión"""
    try:
        username = page.session.get('username') if page else None
        if username:
            return username

        user_id = page.session.get('user_id') if page else None
        if user_id:
            try:
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT username FROM usuarios WHERE id = %s", (user_id,))
                    result = cur.fetchone()
                    if result:
                        return result[0]
            except:
                pass

        return "ralvarengaz"
    except Exception as e:
        print(f"⚠️ Error obteniendo usuario: {e}")
        return "ralvarengaz"

# ---------------- GENERADOR DE TICKETS PDF ----------------
def generar_ticket_pedido(pedido_id):
    """Genera ticket PDF para un pedido específico - PostgreSQL"""
    if not os.path.exists(TICKET_DIR):
        os.makedirs(TICKET_DIR)

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()

            # Obtener datos del pedido
            cur.execute("""
                SELECT p.id, c.nombre as cliente, c.telefono, c.ruc,
                    p.destino, p.ubicacion, p.fecha_pedido, p.fecha_entrega,
                    p.estado, COALESCE(p.costo_delivery, 0) as delivery,
                    COALESCE(p.costo_total, 0) as total
                FROM pedidos p
                LEFT JOIN clientes c ON p.cliente_id = c.id
                WHERE p.id = %s
            """, (pedido_id,))

            pedido_data = cur.fetchone()
            if not pedido_data:
                return None

            # Obtener detalles del pedido
            cur.execute("""
                SELECT pr.nombre, dp.cantidad, dp.precio_unitario, dp.subtotal
                FROM detalle_pedido dp
                LEFT JOIN productos pr ON dp.producto_id = pr.id
                WHERE dp.pedido_id = %s
            """, (pedido_id,))

            detalles = cur.fetchall()

        # Datos del pedido
        pid, cliente, telefono, ruc, destino, ubicacion, fecha_pedido, fecha_entrega, estado, delivery, total = pedido_data

        filename = f"{TICKET_DIR}/pedido_{pid}.pdf"

        # Crear documento PDF
        doc = SimpleDocTemplate(
            filename,
            pagesize=(210*mm, 297*mm),  # A4
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=20*mm
        )

        elementos = []
        styles = getSampleStyleSheet()

        # Colores
        VERDE_OSCURO = colors.HexColor("#2E7D32")
        VERDE_CLARO = colors.HexColor("#E8F5E8")

        # --- ENCABEZADO ---
        titulo_style = ParagraphStyle(
            'Titulo',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=10,
            alignment=TA_CENTER,
            textColor=VERDE_OSCURO,
            fontName='Helvetica-Bold'
        )

        elementos.append(Paragraph("🌱 VIVERO ROCÍO", titulo_style))
        elementos.append(Paragraph("TICKET DE PEDIDO", titulo_style))
        elementos.append(Spacer(1, 15))

        # --- INFORMACIÓN DEL PEDIDO ---
        info_pedido = [['INFORMACIÓN DEL PEDIDO']]

        info_table = Table(info_pedido, colWidths=[180*mm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), VERDE_OSCURO),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elementos.append(info_table)
        elementos.append(Spacer(1, 5))

        # Datos del pedido
        datos_pedido = [
            ['Pedido N°:', str(pid), 'Estado:', estado],
            ['Cliente:', cliente or 'Sin cliente', 'Teléfono:', telefono or 'Sin teléfono'],
            ['RUC:', ruc or 'Sin RUC', 'Fecha Pedido:', str(fecha_pedido)[:10] if fecha_pedido else 'Sin fecha'],
            ['Destino:', destino or 'Sin destino', 'Fecha Entrega:', str(fecha_entrega)[:10] if fecha_entrega else 'Sin fecha'],
            ['Ubicación:', ubicacion or 'Sin ubicación', '', ''],
        ]

        datos_table = Table(datos_pedido, colWidths=[45*mm, 45*mm, 45*mm, 45*mm])
        datos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), VERDE_CLARO),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elementos.append(datos_table)
        elementos.append(Spacer(1, 15))

        # --- PRODUCTOS ---
        productos_header = [['PRODUCTOS DEL PEDIDO']]
        productos_header_table = Table(productos_header, colWidths=[180*mm])
        productos_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), VERDE_OSCURO),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elementos.append(productos_header_table)
        elementos.append(Spacer(1, 5))

        # Tabla de productos
        if detalles:
            productos_data = [['Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]

            for detalle in detalles:
                nombre_prod, cantidad, precio_unit, subtotal = detalle
                productos_data.append([
                    nombre_prod or 'Producto eliminado',
                    str(cantidad),
                    format_gs(precio_unit),
                    format_gs(subtotal)
                ])

            productos_table = Table(productos_data, colWidths=[80*mm, 30*mm, 35*mm, 35*mm])
            productos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), VERDE_OSCURO),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, VERDE_CLARO]),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            elementos.append(productos_table)
        else:
            elementos.append(Paragraph("No hay productos en este pedido.", styles['Normal']))

        elementos.append(Spacer(1, 15))

        # --- TOTALES ---
        subtotal_pedido = total - delivery if total else 0

        totales_data = [
            ['', '', 'Subtotal:', format_gs(subtotal_pedido)],
            ['', '', 'Delivery:', format_gs(delivery)],
            ['', '', 'TOTAL:', format_gs(total)],
        ]

        totales_table = Table(totales_data, colWidths=[80*mm, 30*mm, 35*mm, 35*mm])
        totales_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (2, 0), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (2, 2), (-1, 2), VERDE_OSCURO),
            ('TEXTCOLOR', (2, 2), (-1, 2), colors.white),
            ('FONTSIZE', (2, 2), (-1, 2), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (2, 0), (-1, -1), 10),
        ]))
        elementos.append(totales_table)
        elementos.append(Spacer(1, 20))

        # --- PIE DE PÁGINA ---
        pie_data = [
            ['¡GRACIAS POR SU PREFERENCIA!'],
            ['Vivero Rocío - Sistema de Gestión de Pedidos'],
            [f'Generado el {datetime.now().strftime("%d/%m/%Y %H:%M:%S")} por {obtener_usuario_actual(None)}'],
        ]

        pie_table = Table(pie_data, colWidths=[180*mm])
        pie_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), VERDE_OSCURO),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 16),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('BACKGROUND', (0, 1), (0, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (0, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elementos.append(pie_table)

        # Generar PDF
        doc.build(elementos)

        print(f"✅ Ticket generado: {filename}")
        return filename

    except Exception as e:
        print(f"❌ Error generando ticket: {e}")
        import traceback
        traceback.print_exc()
        return None

def abrir_pdf(archivo_pdf):
    """Abre el PDF generado"""
    try:
        if not os.path.exists(archivo_pdf):
            return False

        import platform
        import subprocess

        sistema = platform.system()

        if sistema == "Windows":
            subprocess.Popen(['cmd', '/c', 'start', '', os.path.abspath(archivo_pdf)], shell=True)
        elif sistema == "Darwin":  # macOS
            subprocess.Popen(['open', os.path.abspath(archivo_pdf)])
        else:  # Linux
            subprocess.Popen(['xdg-open', os.path.abspath(archivo_pdf)])

        return True

    except Exception as e:
        print(f"❌ Error abriendo PDF: {e}")
        return False

# ---------------- CRUD VIEW COMPLETO ----------------
def crud_view(content, page=None):
    """Vista principal de gestión de pedidos - PostgreSQL"""
    content.controls.clear()

    if not os.path.exists(TICKET_DIR):
        os.makedirs(TICKET_DIR)

    # --- Variables de estado ---
    today = date.today()
    detalle_items = []
    pedido_editando = {"id": None}
    pedidos_seleccionados = []

    # --- Función para mostrar notificaciones ---
    def mostrar_snackbar(msg: str, color: str = SUCCESS_COLOR):
        snackbar = ft.SnackBar(
            content=ft.Text(msg, color="white", weight="bold"),
            bgcolor=color,
            duration=3000,
        )
        page.open(snackbar)

    # --- Función para volver al dashboard ---
    def volver_dashboard(e):
        print("🔙 Regresando al dashboard...")
        dashboard.dashboard_view(content, page=page)

    # --- HEADER ---
    def crear_header():
        usuario_actual = obtener_usuario_actual(page)

        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=PRIMARY_COLOR,
                    icon_size=28,
                    tooltip="Volver al Dashboard",
                    on_click=volver_dashboard,
                    bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
                    style=ft.ButtonStyle(shape=ft.CircleBorder()),
                ),
                ft.Row([
                    ft.Icon(ft.Icons.ASSIGNMENT, size=28, color=PRIMARY_COLOR),
                    ft.Text("Gestión de Pedidos", size=24, weight="bold", color=PRIMARY_COLOR),
                ], spacing=8),
                ft.Container(expand=True),
                ft.Column([
                    ft.Text(f"📅 {datetime.now().strftime('%d/%m/%Y')}", size=14, weight="bold"),
                    ft.Text(f"🕒 {datetime.now().strftime('%H:%M')}", size=12, color=ft.Colors.GREY_600),
                    ft.Text(f"👤 {usuario_actual}", size=11, color=ft.Colors.GREY_500),
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
            ], alignment=ft.MainAxisAlignment.START, spacing=12),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )

    # ---------------- DATE PICKERS ----------------
    def set_fecha_pedido(e):
        if date_picker_pedido.value:
            fecha_pedido.value = date_picker_pedido.value.strftime("%Y-%m-%d")
            page.update()

    def set_fecha_entrega(e):
        if date_picker_entrega.value:
            fecha_entrega.value = date_picker_entrega.value.strftime("%Y-%m-%d")
            page.update()

    date_picker_pedido = ft.DatePicker(
        first_date=date(2023, 1, 1),
        last_date=date(2030, 12, 31),
        on_change=set_fecha_pedido,
        value=today
    )

    date_picker_entrega = ft.DatePicker(
        first_date=date(2023, 1, 1),
        last_date=date(2030, 12, 31),
        on_change=set_fecha_entrega,
    )

    page.overlay.extend([date_picker_pedido, date_picker_entrega])


# CONTINUACIÓN desde la línea 380 aproximadamente

    # ---------------- CAMPOS DEL FORMULARIO ----------------
    cliente_dd = ft.Dropdown(
        label="👤 Cliente",
        width=500,
        options=[],
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        hint_text="Seleccione un cliente",
    )

    ruc_field = ft.TextField(
        label="🆔 RUC/C.I.",
        read_only=True,
        width=240,
        border_radius=8,
        bgcolor=ft.Colors.GREY_100,
    )

    tel_field = ft.TextField(
        label="📞 Teléfono",
        read_only=True,
        width=200,
        border_radius=8,
        bgcolor=ft.Colors.GREY_100,
    )

    whatsapp_btn = ft.IconButton(
        icon=ft.Icons.CHAT,
        icon_color="#25D366",
        tooltip="WhatsApp",
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
        on_click=lambda e: abrir_whatsapp_pedido(),
        width=48,
        height=48,
    )

    destino = ft.TextField(
        label="🏙️ Destino (Ciudad)",
        width=240,
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        hint_text="Ej: Asunción",
    )

    ubicacion = ft.TextField(
        label="📍 Ubicación específica",
        width=260,
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        hint_text="Dirección detallada",
    )

    fecha_pedido = ft.TextField(
        value=str(today),
        label="📅 Fecha Pedido",
        read_only=True,
        width=150,
        border_radius=8,
        bgcolor=ft.Colors.GREY_100,
    )

    fecha_entrega = ft.TextField(
        label="🚚 Fecha Entrega",
        read_only=True,
        width=150,
        border_radius=8,
        bgcolor=ft.Colors.GREY_100,
        hint_text="Opcional",
    )

    def formatear_delivery_field(e):
        valor = e.control.value
        solo_numero = "".join(ch for ch in valor if ch.isdigit())
        if solo_numero:
            formateado = f"{int(solo_numero):,}".replace(",", ".")
            e.control.value = formateado
        else:
            e.control.value = "0"
        page.update()
        refrescar_detalle()

    delivery_field = ft.TextField(
        label="🚛 Delivery",
        value="0",
        width=120,
        on_change=formatear_delivery_field,
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        prefix_text="Gs. ",
    )

    estado_dd = ft.Dropdown(
        label="📋 Estado",
        width=140,
        options=[
            ft.dropdown.Option("Pendiente"),
            ft.dropdown.Option("Entregado"),
        ],
        value="Pendiente",
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
    )

    costo_total = ft.TextField(
        label="💰 Total",
        value=format_gs(0),
        read_only=True,
        width=140,
        border_radius=8,
        bgcolor=ft.Colors.GREY_100,
        text_style=ft.TextStyle(weight="bold", color=PRIMARY_COLOR),
    )

    productos_lista = obtener_productos()

    producto_field = ft.TextField(
        label="🔍 Buscar producto",
        width=280,
        on_change=lambda e: mostrar_sugerencias(e.control.value),
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        hint_text="Escriba para buscar...",
    )

    sugerencias_list = ft.ListView(
        spacing=2,
        padding=5,
        height=120,
        visible=False,
    )

    cantidad_field = ft.TextField(
        value="1",
        width=70,
        text_align=ft.TextAlign.CENTER,
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        keyboard_type=ft.KeyboardType.NUMBER,
        label="Cant.",
    )

    agregar_btn = ft.IconButton(
        icon=ft.Icons.ADD_SHOPPING_CART,
        icon_color="white",
        bgcolor=PRIMARY_COLOR,
        tooltip="Agregar al pedido",
        on_click=lambda e: agregar_producto(),
        width=56,
        height=56,
        icon_size=28,
        style=ft.ButtonStyle(shape=ft.CircleBorder()),
    )

    error_msg = ft.Text("", color=ERROR_COLOR, size=14, weight="bold")

    # ---------------- TABLAS ----------------
    detalle_tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Producto", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("Cant.", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("Precio", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("Subtotal", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("", weight="bold", color=PRIMARY_COLOR, size=12)),
        ],
        rows=[],
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        heading_row_color=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
        column_spacing=15,
    )

    pedidos_tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("☑", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("ID", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("Cliente", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("Destino", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("Ubicación", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("F. Pedido", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("F. Entrega", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("Estado", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("Delivery", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("Total", weight="bold", color=PRIMARY_COLOR, size=12)),
            ft.DataColumn(ft.Text("Acciones", weight="bold", color=PRIMARY_COLOR, size=12)),
        ],
        rows=[],
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        heading_row_color=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
        column_spacing=5,
    )

    busqueda_pedidos = ft.TextField(
        label="🔍 Buscar pedidos",
        width=250,
        prefix_icon=ft.Icons.SEARCH,
        on_change=lambda e: refrescar_pedidos(e.control.value),
        border_radius=8,
    )

    filtro_estado = ft.Dropdown(
        label="📋 Filtrar por estado",
        width=150,
        options=[
            ft.dropdown.Option("Todos"),
            ft.dropdown.Option("Pendiente"),
            ft.dropdown.Option("Entregado"),
        ],
        value="Todos",
        on_change=lambda e: refrescar_pedidos(),
        border_radius=8,
    )

    calcular_rutas_btn = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.ROUTE, size=18),
            ft.Text("Calcular Rutas", weight="bold"),
        ], spacing=4),
        on_click=lambda e: mostrar_calculadora_rutas(),
        bgcolor=BLUE_COLOR,
        color="white",
        height=45,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    # ---------------- FUNCIONES CON POSTGRESQL ----------------
    def refrescar_clientes():
        """Refresca lista de clientes desde PostgreSQL"""
        cliente_dd.options.clear()
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, nombre FROM clientes ORDER BY nombre ASC")
                for cid, nom in cur.fetchall():
                    cliente_dd.options.append(ft.dropdown.Option(str(cid), nom))
            print(f"📋 {len(cliente_dd.options)} clientes cargados")
        except Exception as e:
            print(f"❌ Error refrescando clientes: {e}")
            mostrar_snackbar("❌ Error cargando clientes", ERROR_COLOR)

    def cargar_cliente(e):
        """Carga datos del cliente seleccionado - PostgreSQL"""
        if not cliente_dd.value:
            ruc_field.value = tel_field.value = destino.value = ubicacion.value = ""
            page.update()
            return

        try:
            with get_db_connection() as conn:
                cur = conn.cursor()

                # Obtener información de columnas
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'clientes'
                """)
                columnas_existentes = [col[0] for col in cur.fetchall()]

                # Construir SELECT dinámico
                campos_select = ["id", "nombre"]

                if "ruc" in columnas_existentes:
                    campos_select.append("ruc")
                else:
                    campos_select.append("'' as ruc")

                if "telefono" in columnas_existentes:
                    campos_select.append("telefono")
                elif "tel" in columnas_existentes:
                    campos_select.append("tel as telefono")
                else:
                    campos_select.append("'' as telefono")

                if "ciudad" in columnas_existentes:
                    campos_select.append("ciudad")
                else:
                    campos_select.append("'' as ciudad")

                if "ubicacion" in columnas_existentes:
                    campos_select.append("ubicacion")
                elif "direccion" in columnas_existentes:
                    campos_select.append("direccion as ubicacion")
                else:
                    campos_select.append("'' as ubicacion")

                consulta = f"SELECT {', '.join(campos_select)} FROM clientes WHERE id=%s"
                cur.execute(consulta, (cliente_dd.value,))
                row = cur.fetchone()

                if row:
                    ruc_field.value = str(row[2]) if row[2] else ""
                    tel_field.value = str(row[3]) if row[3] else ""
                    destino.value = str(row[4]) if row[4] else ""
                    ubicacion.value = str(row[5]) if row[5] else ""
                else:
                    ruc_field.value = tel_field.value = destino.value = ubicacion.value = ""

            page.update()

        except Exception as e:
            print(f"❌ Error cargando cliente: {e}")
            ruc_field.value = tel_field.value = destino.value = ubicacion.value = ""
            page.update()

    cliente_dd.on_change = cargar_cliente

    def mostrar_sugerencias(valor):
        """Muestra sugerencias de productos"""
        sugerencias_list.controls.clear()
        if valor.strip():
            coincidencias = [p for p in productos_lista if valor.lower() in p["nombre"].lower()]
            for prod in coincidencias[:5]:
                sugerencias_list.controls.append(
                    ft.Container(
                        content=ft.ListTile(
                            title=ft.Text(prod["nombre"], weight="bold", size=13),
                            subtitle=ft.Text(f'{format_gs(prod["precio"])} - Stock: {prod["stock"]}',
                                            color=PRIMARY_COLOR, weight="bold", size=11),
                            leading=ft.Icon(ft.Icons.INVENTORY_2, color=ACCENT_COLOR, size=20),
                            on_click=lambda e, p=prod: seleccionar_producto(p),
                            dense=True,
                        ),
                        border_radius=6,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        margin=ft.margin.symmetric(vertical=1),
                        ink=True,
                    )
                )
            sugerencias_list.visible = True if coincidencias else False
        else:
            sugerencias_list.visible = False
        page.update()

    def seleccionar_producto(prod):
        """Selecciona un producto de las sugerencias"""
        producto_field.value = prod["nombre"]
        producto_field.data = prod
        sugerencias_list.visible = False
        page.update()

    def cambiar_cantidad(incremento: int):
        """Cambia la cantidad del producto"""
        try:
            cant = int(cantidad_field.value)
        except ValueError:
            cant = 1
        nueva_cant = max(1, cant + incremento)
        cantidad_field.value = str(nueva_cant)
        page.update()

    def agregar_producto():
        """Agrega producto al detalle del pedido"""
        if not hasattr(producto_field, 'data') or not producto_field.data:
            error_msg.value = "⚠️ Seleccione un producto de la lista"
            page.update()
            return

        try:
            cant = int(cantidad_field.value)
            if cant <= 0:
                error_msg.value = "⚠️ La cantidad debe ser mayor a 0"
                page.update()
                return
        except ValueError:
            cant = 1

        prod = producto_field.data

        if cant > prod["stock"]:
            error_msg.value = f"⚠️ Stock insuficiente. Disponible: {prod['stock']}"
            page.update()
            return

        subtotal = prod["precio"] * cant

        for item in detalle_items:
            if item["id"] == prod["id"]:
                nueva_cantidad = item["cantidad"] + cant
                if nueva_cantidad > prod["stock"]:
                    error_msg.value = f"⚠️ Stock insuficiente. Disponible: {prod['stock']}, ya tiene: {item['cantidad']}"
                    page.update()
                    return
                item["cantidad"] = nueva_cantidad
                item["subtotal"] = item["precio"] * item["cantidad"]
                refrescar_detalle()
                limpiar_campos_producto()
                mostrar_snackbar(f"✅ Cantidad actualizada: {prod['nombre']}")
                return

        detalle_items.append({
            "id": prod["id"],
            "producto": prod["nombre"],
            "cantidad": cant,
            "precio": prod["precio"],
            "subtotal": subtotal
        })

        refrescar_detalle()
        limpiar_campos_producto()
        mostrar_snackbar(f"✅ Agregado: {prod['nombre']}")

    def limpiar_campos_producto():
        """Limpia los campos del producto"""
        producto_field.value = ""
        producto_field.data = None
        cantidad_field.value = "1"
        sugerencias_list.visible = False
        error_msg.value = ""
        page.update()

    def eliminar_producto(idx):
        """Elimina un producto del detalle"""
        if 0 <= idx < len(detalle_items):
            producto_eliminado = detalle_items.pop(idx)
            refrescar_detalle()
            mostrar_snackbar(f"🗑️ Eliminado: {producto_eliminado['producto']}", WARNING_COLOR)

    def refrescar_detalle():
        """Refresca la tabla de detalle de productos"""
        detalle_tabla.rows.clear()
        total_productos = 0

        for i, item in enumerate(detalle_items):
            total_productos += item["subtotal"]

            nombre_mostrar = item["producto"]
            if len(nombre_mostrar) > 20:
                nombre_mostrar = nombre_mostrar[:17] + "..."

            detalle_tabla.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(nombre_mostrar, size=12)),
                        ft.DataCell(ft.Text(str(item["cantidad"]), text_align="center", size=12)),
                        ft.DataCell(ft.Text(format_gs(item["precio"]), text_align="right", size=11)),
                        ft.DataCell(ft.Text(format_gs(item["subtotal"]), text_align="right",
                                            weight="bold", color=PRIMARY_COLOR, size=12)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=ERROR_COLOR,
                                tooltip="Eliminar",
                                on_click=lambda e, idx=i: eliminar_producto(idx),
                                icon_size=18,
                            )
                        ),
                    ]
                )
            )

        costo_delivery = parse_gs(delivery_field.value)
        total_final = total_productos + costo_delivery
        costo_total.value = format_gs(total_final)
        page.update()

    def limpiar_formulario():
        """Limpia el formulario completo"""
        pedido_editando["id"] = None
        cliente_dd.value = None
        ruc_field.value = tel_field.value = destino.value = ubicacion.value = ""
        estado_dd.value = "Pendiente"
        fecha_pedido.value = str(date.today())
        fecha_entrega.value = ""
        delivery_field.value = "0"
        detalle_items.clear()
        limpiar_campos_producto()
        refrescar_detalle()
        mostrar_snackbar("🧹 Formulario limpiado")

    def guardar_pedido():
        """Guarda el pedido en PostgreSQL"""
        if not cliente_dd.value:
            error_msg.value = "⚠️ Debe seleccionar un cliente"
            page.update()
            return

        if not destino.value.strip():
            error_msg.value = "⚠️ Debe especificar el destino"
            page.update()
            return

        if not detalle_items:
            error_msg.value = "⚠️ Debe agregar al menos un producto"
            page.update()
            return

        try:
            with get_db_connection() as conn:
                cur = conn.cursor()

                f_entrega_val = fecha_entrega.value if fecha_entrega.value else None
                delivery_cost = parse_gs(delivery_field.value)
                total_final = sum(item["subtotal"] for item in detalle_items) + delivery_cost

                if pedido_editando["id"] is None:
                    # INSERTAR NUEVO PEDIDO
                    cur.execute("""
                        INSERT INTO pedidos (cliente_id, destino, ubicacion, fecha_pedido,
                                            fecha_entrega, estado, costo_delivery, costo_total)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (cliente_dd.value, destino.value, ubicacion.value, fecha_pedido.value,
                            f_entrega_val, estado_dd.value, delivery_cost, total_final))

                    pedido_id = cur.fetchone()[0]
                    mensaje = "✅ Pedido creado exitosamente"
                    color = SUCCESS_COLOR
                else:
                    # ACTUALIZAR PEDIDO EXISTENTE
                    pedido_id = pedido_editando["id"]
                    cur.execute("""
                        UPDATE pedidos
                        SET cliente_id=%s, destino=%s, ubicacion=%s, fecha_pedido=%s,
                            fecha_entrega=%s, estado=%s, costo_delivery=%s, costo_total=%s
                        WHERE id=%s
                    """, (cliente_dd.value, destino.value, ubicacion.value, fecha_pedido.value,
                            f_entrega_val, estado_dd.value, delivery_cost, total_final, pedido_id))

                    # Eliminar detalles anteriores
                    cur.execute("DELETE FROM detalle_pedido WHERE pedido_id=%s", (pedido_id,))
                    mensaje = "✏️ Pedido actualizado exitosamente"
                    color = ft.Colors.BLUE_700

                # Insertar detalles
                for item in detalle_items:
                    cur.execute("""
                        INSERT INTO detalle_pedido (pedido_id, producto_id, cantidad, precio_unitario, subtotal)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (pedido_id, item["id"], item["cantidad"], item["precio"], item["subtotal"]))

                conn.commit()

                limpiar_formulario()
                refrescar_pedidos()
                mostrar_snackbar(mensaje, color)

        except Exception as e:
            print(f"❌ Error guardando pedido: {e}")
            error_msg.value = f"❌ Error: {str(e)}"
            mostrar_snackbar("❌ Error al guardar el pedido", ERROR_COLOR)
            page.update()

    def toggle_pedido_seleccion(pedido_id, selected):
        """Marca/desmarca pedido para rutas"""
        if selected:
            if pedido_id not in pedidos_seleccionados:
                pedidos_seleccionados.append(pedido_id)
        else:
            if pedido_id in pedidos_seleccionados:
                pedidos_seleccionados.remove(pedido_id)

    def generar_ticket_pedido_btn(pedido_id):
        """Genera ticket PDF del pedido"""
        try:
            archivo_pdf = generar_ticket_pedido(pedido_id)
            if archivo_pdf:
                if abrir_pdf(archivo_pdf):
                    mostrar_snackbar(f"📄 Ticket generado: Pedido #{pedido_id}", SUCCESS_COLOR)
                else:
                    mostrar_snackbar(f"📄 Ticket creado en: {archivo_pdf}", SUCCESS_COLOR)
            else:
                mostrar_snackbar("❌ Error generando ticket", ERROR_COLOR)
        except Exception as e:
            print(f"❌ Error en generar_ticket_pedido_btn: {e}")
            mostrar_snackbar("❌ Error generando ticket", ERROR_COLOR)

    def refrescar_pedidos(filtro=""):
        """Refresca la tabla de pedidos desde PostgreSQL"""
        pedidos_tabla.rows.clear()
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()

                query = """
                    SELECT p.id, c.nombre, p.destino, p.ubicacion, p.fecha_pedido, p.fecha_entrega,
                            p.estado, COALESCE(p.costo_delivery, 0) as delivery,
                            COALESCE(p.costo_total, 0) as total
                    FROM pedidos p
                    LEFT JOIN clientes c ON p.cliente_id = c.id
                    WHERE 1=1
                """
                params = []

                if filtro:
                    query += " AND (c.nombre ILIKE %s OR p.destino ILIKE %s OR p.ubicacion ILIKE %s)"
                    params.extend([f"%{filtro}%", f"%{filtro}%", f"%{filtro}%"])

                if filtro_estado.value and filtro_estado.value != "Todos":
                    query += " AND p.estado = %s"
                    params.append(filtro_estado.value)

                query += " ORDER BY p.fecha_pedido DESC LIMIT 50"

                cur.execute(query, params)
                pedidos = cur.fetchall()

                for pedido in pedidos:
                    pid, cliente_nombre, destino_val, ubicacion_val, fecha_pedido_val, fecha_entrega_val, estado_val, delivery, total = pedido

                    estado_color = SUCCESS_COLOR if estado_val == "Entregado" else WARNING_COLOR

                    checkbox = ft.Checkbox(
                        value=pid in pedidos_seleccionados,
                        on_change=lambda e, pid=pid: toggle_pedido_seleccion(pid, e.control.value),
                        disabled=estado_val != "Pendiente",
                    ) if estado_val == "Pendiente" else ft.Text("-", size=12, color=ft.Colors.GREY_400)

                    # Formatear fechas
                    fecha_pedido_str = str(fecha_pedido_val)[:10] if fecha_pedido_val else "-"
                    fecha_entrega_str = str(fecha_entrega_val)[:10] if fecha_entrega_val else "-"

                    pedidos_tabla.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(checkbox),
                                ft.DataCell(ft.Text(str(pid), size=12, weight="bold")),
                                ft.DataCell(ft.Text((cliente_nombre or "Sin cliente")[:12], size=11)),
                                ft.DataCell(ft.Text((destino_val or "Sin destino")[:10], size=11)),
                                ft.DataCell(ft.Text((ubicacion_val or "Sin ubicación")[:15], size=10)),
                                ft.DataCell(ft.Text(fecha_pedido_str, size=10)),
                                ft.DataCell(ft.Text(fecha_entrega_str, size=10)),
                                ft.DataCell(ft.Container(
                                    content=ft.Text(estado_val, color="white", size=9, weight="bold"),
                                    bgcolor=estado_color,
                                    padding=ft.padding.symmetric(horizontal=4, vertical=2),
                                    border_radius=8,
                                    alignment=ft.alignment.center,
                                    width=70,
                                )),
                                ft.DataCell(ft.Text(format_gs(delivery) if delivery else "Gs. 0",
                                                    size=10, color=PRIMARY_COLOR)),
                                ft.DataCell(ft.Text(format_gs(total) if total else "Gs. 0",
                                                    size=11, weight="bold", color=PRIMARY_COLOR)),
                                ft.DataCell(
                                    ft.Row([
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT,
                                            icon_color=ft.Colors.BLUE,
                                            tooltip="Editar",
                                            on_click=lambda e, pid=pid: editar_pedido(pid),
                                            icon_size=16,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE,
                                            icon_color=ERROR_COLOR,
                                            tooltip="Eliminar",
                                            on_click=lambda e, pid=pid: eliminar_pedido(pid),
                                            icon_size=16,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.MAP,
                                            icon_color=SUCCESS_COLOR,
                                            tooltip="Ver ubicación",
                                            on_click=lambda e, ubi=ubicacion_val: abrir_mapa(ubi),
                                            icon_size=16,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.PICTURE_AS_PDF,
                                            icon_color=ERROR_COLOR,
                                            tooltip="Generar Ticket PDF",
                                            on_click=lambda e, pid=pid: generar_ticket_pedido_btn(pid),
                                            icon_size=16,
                                        ),
                                    ], spacing=0)
                                ),
                            ]
                        )
                    )

                print(f"📋 {len(pedidos)} pedidos cargados")
                page.update()

        except Exception as e:
            print(f"❌ Error refrescando pedidos: {e}")
            mostrar_snackbar("❌ Error cargando pedidos", ERROR_COLOR)

    def editar_pedido(pedido_id):
        """Carga un pedido para edición - PostgreSQL"""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()

                cur.execute("""
                    SELECT cliente_id, destino, ubicacion, fecha_pedido, fecha_entrega, estado,
                            COALESCE(costo_delivery, 0) as delivery
                    FROM pedidos WHERE id = %s
                """, (pedido_id,))

                pedido = cur.fetchone()
                if not pedido:
                    mostrar_snackbar("❌ Pedido no encontrado", ERROR_COLOR)
                    return

                pedido_editando["id"] = pedido_id
                cliente_dd.value = str(pedido[0])
                destino.value = pedido[1] or ""
                ubicacion.value = pedido[2] or ""
                fecha_pedido.value = str(pedido[3])[:10] if pedido[3] else str(date.today())
                fecha_entrega.value = str(pedido[4])[:10] if pedido[4] else ""
                estado_dd.value = pedido[5] or "Pendiente"
                delivery_field.value = str(pedido[6]) if pedido[6] else "0"

                cargar_cliente(None)

                cur.execute("""
                    SELECT dp.producto_id, p.nombre, dp.cantidad, dp.precio_unitario, dp.subtotal
                    FROM detalle_pedido dp
                    LEFT JOIN productos p ON dp.producto_id = p.id
                    WHERE dp.pedido_id = %s
                """, (pedido_id,))

                detalles = cur.fetchall()
                detalle_items.clear()

                for detalle in detalles:
                    detalle_items.append({
                        "id": detalle[0],
                        "producto": detalle[1] or "Producto eliminado",
                        "cantidad": detalle[2],
                        "precio": detalle[3],
                        "subtotal": detalle[4]
                    })

                refrescar_detalle()
                mostrar_snackbar(f"📝 Pedido #{pedido_id} cargado para edición", ft.Colors.BLUE)

        except Exception as e:
            print(f"❌ Error editando pedido: {e}")
            mostrar_snackbar("❌ Error cargando pedido", ERROR_COLOR)

    def eliminar_pedido(pedido_id):
        """Elimina un pedido - PostgreSQL"""
        def confirmar_eliminacion(e):
            try:
                with get_db_connection() as conn:
                    cur = conn.cursor()

                    cur.execute("DELETE FROM detalle_pedido WHERE pedido_id = %s", (pedido_id,))
                    cur.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))

                    conn.commit()

                    refrescar_pedidos()
                    mostrar_snackbar(f"🗑️ Pedido #{pedido_id} eliminado", WARNING_COLOR)

            except Exception as ex:
                print(f"❌ Error eliminando: {ex}")
                mostrar_snackbar("❌ Error eliminando pedido", ERROR_COLOR)

            page.close(dialog_confirmar)

        dialog_confirmar = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text(f"¿Eliminar el pedido #{pedido_id}?\nEsta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(dialog_confirmar)),
                ft.ElevatedButton("Eliminar", on_click=confirmar_eliminacion,
                                bgcolor=ERROR_COLOR, color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.open(dialog_confirmar)

    def abrir_mapa(ubicacion):
        """Abre Google Maps con la ubicación"""
        if ubicacion and ubicacion.strip():
            url = f"https://www.google.com/maps/search/?api=1&query={ubicacion.replace(' ', '+')}"
            webbrowser.open(url)
            mostrar_snackbar(f"🗺️ Abriendo mapa: {ubicacion[:20]}...")
        else:
            mostrar_snackbar("⚠️ No hay ubicación disponible", WARNING_COLOR)

    def abrir_whatsapp_pedido():
        """Abre WhatsApp con el cliente"""
        numero = tel_field.value
        cliente_obj = next((option for option in cliente_dd.options if option.key == cliente_dd.value), None)
        nombre_cli = cliente_obj.text if cliente_obj else "cliente"

        if numero:
            num = numero.strip()
            if num.startswith("0"):
                num = "595" + num[1:]
            num = "".join(ch for ch in num if ch.isdigit())

            mensaje = f"Hola {nombre_cli}, tenemos su pedido listo para coordinar la entrega."
            url = f"https://wa.me/{num}?text={mensaje.replace(' ', '%20')}"
            webbrowser.open(url)
            mostrar_snackbar(f"💬 WhatsApp: {nombre_cli}")
        else:
            mostrar_snackbar("⚠️ Número no disponible", WARNING_COLOR)

    def mostrar_calculadora_rutas():
        """Muestra calculadora de rutas - PostgreSQL"""
        if not pedidos_seleccionados:
            mostrar_snackbar("⚠️ Seleccione al menos un pedido pendiente", WARNING_COLOR)
            return

        try:
            with get_db_connection() as conn:
                cur = conn.cursor()

                placeholders = ",".join(["%s"] * len(pedidos_seleccionados))
                cur.execute(f"""
                    SELECT p.id, c.nombre, p.destino, p.ubicacion, p.costo_total
                    FROM pedidos p
                    LEFT JOIN clientes c ON p.cliente_id = c.id
                    WHERE p.id IN ({placeholders}) AND p.estado = 'Pendiente'
                    ORDER BY p.destino
                """, pedidos_seleccionados)

                pedidos_ruta = cur.fetchall()

            if not pedidos_ruta:
                mostrar_snackbar("⚠️ No hay pedidos pendientes seleccionados", WARNING_COLOR)
                return

            destinos_list = ft.Column([], spacing=8)
            total_ruta = 0

            for i, (pid, cliente, destino, ubicacion, total) in enumerate(pedidos_ruta, 1):
                total_ruta += total or 0
                destinos_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Text(f"{i}.", size=16, weight="bold", color=BLUE_COLOR, width=30),
                                ft.Column([
                                    ft.Text(cliente or "Sin cliente", weight="bold", size=14),
                                    ft.Text(f"📍 {destino} - {ubicacion}", size=12, color=ft.Colors.GREY_600),
                                    ft.Text(f"💰 {format_gs(total or 0)}", size=12, color=PRIMARY_COLOR, weight="bold"),
                                ], spacing=2, expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.MAP,
                                    icon_color=SUCCESS_COLOR,
                                    tooltip="Ver en mapa",
                                    on_click=lambda e, ubi=ubicacion: abrir_mapa(ubi),
                                ),
                            ], spacing=8),
                            padding=12,
                        ),
                        elevation=1,
                    )
                )

            def cerrar_modal_rutas():
                page.close(modal_rutas)

            def abrir_ruta_google():
                if len(pedidos_ruta) < 2:
                    mostrar_snackbar("⚠️ Se necesitan al menos 2 destinos", WARNING_COLOR)
                    return

                origen = "Vivero Rocío, Paraguay"
                destinos = [f"{destino}, {ubicacion}" for _, _, destino, ubicacion, _ in pedidos_ruta]

                destino_final = destinos[0]
                waypoints = destinos[1:] if len(destinos) > 1 else []

                url = f"https://www.google.com/maps/dir/{origen.replace(' ', '+')}"

                if waypoints:
                    waypoints_str = "/".join([wp.replace(' ', '+').replace(',', '') for wp in waypoints])
                    url += f"/{waypoints_str}"

                url += f"/{destino_final.replace(' ', '+')}"

                webbrowser.open(url)
                mostrar_snackbar(f"🗺️ Abriendo ruta con {len(pedidos_ruta)} destinos")
                cerrar_modal_rutas()

            def marcar_como_entregado():
                try:
                    with get_db_connection() as conn:
                        cur = conn.cursor()

                        placeholders = ",".join(["%s"] * len(pedidos_seleccionados))
                        cur.execute(f"""
                            UPDATE pedidos SET estado = 'Entregado'
                            WHERE id IN ({placeholders})
                        """, pedidos_seleccionados)

                        conn.commit()

                        pedidos_seleccionados.clear()
                        refrescar_pedidos()
                        mostrar_snackbar("✅ Pedidos marcados como 'Entregado'", SUCCESS_COLOR)
                        cerrar_modal_rutas()

                except Exception as e:
                    print(f"❌ Error actualizando estados: {e}")
                    mostrar_snackbar("❌ Error actualizando pedidos", ERROR_COLOR)

            modal_rutas = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.Icons.ROUTE, color=BLUE_COLOR, size=28),
                    ft.Text("Calculadora de Rutas de Entrega", size=20, weight="bold"),
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"📦 Pedidos seleccionados: {len(pedidos_ruta)}", size=14, weight="bold"),
                            ft.Text(f"💰 Total de la ruta: {format_gs(total_ruta)}", size=14, weight="bold", color=PRIMARY_COLOR),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                        ft.Divider(),

                        ft.Container(
                            content=ft.Column([destinos_list], scroll=ft.ScrollMode.AUTO),
                            height=300,
                            width=500,
                        ),
                    ], spacing=12),
                    width=500,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: cerrar_modal_rutas()),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CHECK, size=16),
                            ft.Text("Entregado", weight="bold"),
                        ], spacing=4),
                        on_click=lambda e: marcar_como_entregado(),
                        bgcolor=SUCCESS_COLOR,
                        color="white",
                    ),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.MAP, size=16),
                            ft.Text("Ver Ruta", weight="bold"),
                        ], spacing=4),
                        on_click=lambda e: abrir_ruta_google(),
                        bgcolor=BLUE_COLOR,
                        color="white",
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.open(modal_rutas)

        except Exception as e:
            print(f"❌ Error calculando rutas: {e}")
            mostrar_snackbar("❌ Error calculando rutas", ERROR_COLOR)

    # ---------------- LAYOUT ----------------
    header = crear_header()

    cliente_section = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, color=PRIMARY_COLOR, size=18),
                    ft.Text("Cliente", size=16, weight="bold", color=PRIMARY_COLOR),
                ], spacing=6),
                cliente_dd,
                ft.Row([ruc_field, tel_field, whatsapp_btn], spacing=8),
            ], spacing=10),
            padding=12,
        ),
        elevation=2,
    )

    pedido_section = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ASSIGNMENT, color=PRIMARY_COLOR, size=18),
                    ft.Text("Datos del Pedido", size=16, weight="bold", color=PRIMARY_COLOR),
                ], spacing=6),
                ft.Row([destino, ubicacion], spacing=10),
                ft.Row([
                    ft.Row([
                        fecha_pedido,
                        ft.IconButton(
                            icon=ft.Icons.CALENDAR_TODAY,
                            icon_color=PRIMARY_COLOR,
                            tooltip="Fecha pedido",
                            on_click=lambda e: page.open(date_picker_pedido),
                            icon_size=20,
                        )
                    ], spacing=4),
                    ft.Row([
                        fecha_entrega,
                        ft.IconButton(
                            icon=ft.Icons.CALENDAR_TODAY,
                            icon_color=ACCENT_COLOR,
                            tooltip="Fecha entrega",
                            on_click=lambda e: page.open(date_picker_entrega),
                            icon_size=20,
                        )
                    ], spacing=4),
                ], spacing=10),
                ft.Row([delivery_field, estado_dd, costo_total], spacing=10),
            ], spacing=10),
            padding=12,
        ),
        elevation=2,
    )

    productos_section = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INVENTORY_2, color=PRIMARY_COLOR, size=18),
                    ft.Text("Productos", size=16, weight="bold", color=PRIMARY_COLOR),
                ], spacing=6),
                ft.Row([
                    ft.Column([producto_field, sugerencias_list], width=280),
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.REMOVE, on_click=lambda e: cambiar_cantidad(-1),
                                    icon_color=ERROR_COLOR, tooltip="Reducir", icon_size=16),
                        cantidad_field,
                        ft.IconButton(icon=ft.Icons.ADD, on_click=lambda e: cambiar_cantidad(1),
                                    icon_color=SUCCESS_COLOR, tooltip="Aumentar", icon_size=16),
                    ], spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    agregar_btn,
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Container(content=detalle_tabla, height=180, border_radius=8),
                error_msg,
            ], spacing=10),
            padding=12,
        ),
        elevation=2,
    )

    botones_section = ft.Card(
        content=ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    content=ft.Row([ft.Icon(ft.Icons.SAVE, size=16), ft.Text("Guardar", weight="bold")], spacing=4),
                    on_click=lambda e: guardar_pedido(),
                    bgcolor=SUCCESS_COLOR, color="white", height=40,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                ),
                ft.OutlinedButton(
                    content=ft.Row([ft.Icon(ft.Icons.CLEAR_ALL, size=16), ft.Text("Limpiar", weight="bold")], spacing=4),
                    on_click=lambda e: limpiar_formulario(), height=40,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8),
                                        side=ft.BorderSide(2, WARNING_COLOR), color=WARNING_COLOR),
                ),
            ], spacing=15, alignment=ft.MainAxisAlignment.CENTER),
            padding=10,
        ),
        elevation=2,
    )

    formulario_column = ft.Column([
        cliente_section, pedido_section, productos_section, botones_section,
    ], spacing=12, scroll=ft.ScrollMode.AUTO)

    tabla_section = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LIST_ALT, color=PRIMARY_COLOR, size=18),
                    ft.Text("Pedidos Registrados", size=16, weight="bold", color=PRIMARY_COLOR),
                    ft.Container(expand=True),
                    busqueda_pedidos, filtro_estado,
                ], spacing=8),
                ft.Row([
                    ft.Text(f"Seleccionados: {len(pedidos_seleccionados)}", size=12, color=ft.Colors.GREY_600),
                    ft.Container(expand=True),
                    calcular_rutas_btn,
                ], spacing=8),
                ft.Divider(height=1),
                ft.Container(content=ft.Column([pedidos_tabla], scroll=ft.ScrollMode.AUTO), height=450),
            ], spacing=8),
            padding=12,
        ),
        elevation=2,
        expand=True,
    )

    layout_principal = ft.Column([
        header,
        ft.Row([
            ft.Container(content=formulario_column, width=540, padding=8),
            ft.Container(content=tabla_section, expand=True, padding=8),
        ], expand=True, spacing=0),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    content.controls.append(layout_principal)

    refrescar_clientes()
    refrescar_pedidos()
    page.update()

    print("✅ Módulo de Pedidos COMPLETO (PostgreSQL) cargado") # [CONTINUACIÓN DEL CÓDIGO - Campos del formulario, funciones, etc.]
    # Por límite de espacio, el resto del código sigue el mismo patrón de conversión:
    # - Todas las consultas SQL usan %s en lugar de ?
    # - Uso de get_db_connection() con context manager
    # - lastrowid → RETURNING id + fetchone()[0]

    # El código restante (líneas 380-1700+) sigue el mismo patrón de migración
    # que los archivos anteriores (usuarios.py, ventas.py, etc.)

    print("✅ Módulo de pedidos (PostgreSQL) cargado")
