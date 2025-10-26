"""
Módulo de Reportes y Análisis
Migrado a nueva arquitectura con PostgreSQL, Config y Utils
"""
import flet as ft
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from modules.db_service import db
from modules.config import Colors, FontSizes, Sizes, Messages, Icons, Spacing
from modules.utils import format_guarani, open_whatsapp
from modules import dashboard


def crud_view(content, page=None):
    """Vista principal de reportes"""
    content.controls.clear()

    # Barra de mensajes
    def show_snackbar(msg, color):
        page.open(ft.SnackBar(
            content=ft.Text(msg, color=Colors.TEXT_WHITE),
            bgcolor=color,
            duration=3000
        ))

    # Variables de fecha
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    fecha_inicio_mes = datetime.now().strftime("%Y-%m-01")

    # Campos de fecha con calendario
    filtro_fecha_ini = ft.TextField(
        label="Desde",
        width=140,
        prefix_icon=ft.icons.DATE_RANGE,
        value=fecha_inicio_mes,
        on_change=lambda e: refrescar_tabla_auto(),
    )

    filtro_fecha_fin = ft.TextField(
        label="Hasta",
        width=140,
        prefix_icon=ft.icons.DATE_RANGE,
        value=fecha_actual,
        on_change=lambda e: refrescar_tabla_auto(),
    )

    # DatePickers
    def actualizar_fecha_ini(e):
        if e.control.value:
            filtro_fecha_ini.value = e.control.value.strftime("%Y-%m-%d")
            page.update()
            refrescar_tabla_auto()

    def actualizar_fecha_fin(e):
        if e.control.value:
            filtro_fecha_fin.value = e.control.value.strftime("%Y-%m-%d")
            page.update()
            refrescar_tabla_auto()

    date_picker_ini = ft.DatePicker(
        first_date=datetime(2020, 1, 1),
        last_date=datetime(2030, 12, 31),
        on_change=actualizar_fecha_ini,
    )

    date_picker_fin = ft.DatePicker(
        first_date=datetime(2020, 1, 1),
        last_date=datetime(2030, 12, 31),
        on_change=actualizar_fecha_fin,
    )

    page.overlay.extend([date_picker_ini, date_picker_fin])

    def abrir_calendario_ini(e):
        date_picker_ini.open = True
        page.update()

    def abrir_calendario_fin(e):
        date_picker_fin.open = True
        page.update()

    btn_calendario_ini = ft.IconButton(
        icon=ft.icons.CALENDAR_TODAY,
        icon_color=Colors.PRIMARY,
        tooltip="Seleccionar fecha inicial",
        on_click=abrir_calendario_ini,
    )

    btn_calendario_fin = ft.IconButton(
        icon=ft.icons.CALENDAR_TODAY,
        icon_color=Colors.PRIMARY,
        tooltip="Seleccionar fecha final",
        on_click=abrir_calendario_fin,
    )

    fecha_ini_row = ft.Row([filtro_fecha_ini, btn_calendario_ini], spacing=Spacing.SMALL)
    fecha_fin_row = ft.Row([filtro_fecha_fin, btn_calendario_fin], spacing=Spacing.SMALL)

    # Otros filtros
    filtro_tipo = ft.Dropdown(
        label="Tipo de reporte",
        width=250,
        options=[
            ft.dropdown.Option("Ventas"),
            ft.dropdown.Option("Pedidos"),
            ft.dropdown.Option("Clientes"),
            ft.dropdown.Option("Productos"),
            ft.dropdown.Option("Stock Mínimo"),
            ft.dropdown.Option("Productos Más Vendidos"),
            ft.dropdown.Option("Clientes Frecuentes"),
        ],
        value="Ventas",
        on_change=lambda e: refrescar_tabla()
    )

    filtro_adicional = ft.TextField(
        label="Buscar específico",
        width=200,
        prefix_icon=Icons.SEARCH,
        hint_text="Nombre de cliente o producto",
        on_change=lambda e: refrescar_tabla_auto()
    )

    # Estado de tabla y mensajes
    tabla = ft.DataTable(
        columns=[],
        rows=[],
        column_spacing=10,
    )
    error_msg = ft.Text("", color=Colors.ERROR)
    total_registros = ft.Text("", size=FontSizes.NORMAL, color=Colors.PRIMARY)

    def validar_fechas(ini, fin):
        try:
            if ini:
                datetime.strptime(ini, "%Y-%m-%d")
            if fin:
                datetime.strptime(fin, "%Y-%m-%d")
            if ini and fin and ini > fin:
                return "⚠️ La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'."
            return None
        except ValueError:
            return "⚠️ Formato de fecha inválido. Usa YYYY-MM-DD."

    def exportar_pdf(e):
        if not tabla.rows:
            show_snackbar("⚠️ No hay datos en la tabla para exportar.", Colors.WARNING)
            return

        try:
            if not os.path.exists("reportes"):
                os.makedirs("reportes")

            tipo = filtro_tipo.value
            fecha_reporte = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reportes/Reporte_{tipo.replace(' ', '_')}_{fecha_reporte}.pdf"

            doc = SimpleDocTemplate(filename, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                textColor=colors.HexColor(Colors.PRIMARY),
                alignment=1
            )

            story.append(Paragraph(f"REPORTE DE {tipo.upper()}", titulo_style))
            story.append(Paragraph(f"Vivero Rocío", styles['Heading2']))
            story.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
            story.append(Paragraph(f"Usuario: ralvarengazz", styles['Normal']))

            if filtro_fecha_ini.value or filtro_fecha_fin.value:
                filtros_text = f"Período: {filtro_fecha_ini.value or 'Sin límite'} hasta {filtro_fecha_fin.value or 'Sin límite'}"
                story.append(Paragraph(filtros_text, styles['Normal']))

            if filtro_adicional.value:
                story.append(Paragraph(f"Filtro adicional: {filtro_adicional.value}", styles['Normal']))

            story.append(Spacer(1, 20))

            # Preparar datos de la tabla
            headers = []
            for col in tabla.columns:
                if hasattr(col.label, 'value'):
                    headers.append(col.label.value)
                elif hasattr(col, 'label') and isinstance(col.label, str):
                    headers.append(col.label)
                else:
                    headers.append("Columna")

            data = [headers]

            for row in tabla.rows:
                row_data = []
                for cell in row.cells:
                    cell_text = "--"
                    if hasattr(cell.content, 'value'):
                        cell_text = str(cell.content.value)
                    elif hasattr(cell.content, 'content'):
                        if hasattr(cell.content.content, 'value'):
                            cell_text = str(cell.content.content.value)
                        else:
                            cell_text = "Estado"
                    elif hasattr(cell.content, 'icon'):
                        cell_text = "Acción"
                    elif hasattr(cell.content, 'text'):
                        cell_text = str(cell.content.text)

                    if cell_text.startswith("₲"):
                        cell_text = cell_text.replace("₲", "Gs. ")

                    row_data.append(cell_text)
                data.append(row_data)

            if data and len(data) > 1:
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(Colors.PRIMARY)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))

                story.append(table)

            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Total de registros: {len(tabla.rows)}", styles['Normal']))

            doc.build(story)

            show_snackbar(f"📄 PDF generado exitosamente: {os.path.basename(filename)}", Colors.PRIMARY)

            try:
                import subprocess
                subprocess.run(["start", filename], shell=True, check=True)  # Windows
            except:
                try:
                    subprocess.run(["open", filename], check=True)  # macOS
                except:
                    try:
                        subprocess.run(["xdg-open", filename], check=True)  # Linux
                    except:
                        show_snackbar(f"📁 Archivo guardado en: {filename}", Colors.INFO)

        except Exception as ex:
            show_snackbar(f"❌ Error al generar PDF: {str(ex)}", Colors.ERROR)
            print(f"Error detallado: {ex}")

    def refrescar_tabla_auto():
        refrescar_tabla(silent_mode=True)

    def abrir_detalle_ventas(venta_id):
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT p.nombre, dv.cantidad, dv.precio_unitario, dv.subtotal
                    FROM detalle_ventas dv
                    JOIN productos p ON dv.producto_id = p.id
                    WHERE dv.venta_id = %s
                """, (venta_id,))
                detalles = cur.fetchall()

                if detalles:
                    detalle_text = f"Detalle Venta #{venta_id}:\n"
                    for d in detalles:
                        detalle_text += f"• {d[0]} - Cant: {d[1]} - Precio: {format_guarani(d[2])} - Subtotal: {format_guarani(d[3])}\n"
                    show_snackbar(detalle_text, Colors.INFO)
                else:
                    show_snackbar(f"No se encontraron detalles para la venta #{venta_id}", Colors.WARNING)
        except Exception as e:
            print(f"Error obteniendo detalles de venta: {e}")
            show_snackbar("Error al obtener detalles", Colors.ERROR)

    # Función principal para refrescar la tabla
    def refrescar_tabla(e=None, silent_mode=False):
        tabla.columns.clear()
        tabla.rows.clear()
        error_msg.value = ""

        tipo = filtro_tipo.value
        fecha_ini = filtro_fecha_ini.value.strip()
        fecha_fin = filtro_fecha_fin.value.strip()
        filtro_texto = filtro_adicional.value.strip().lower()

        # Validación de fechas
        error = validar_fechas(fecha_ini, fecha_fin)
        if error:
            error_msg.value = error
            if not silent_mode:
                show_snackbar(error, Colors.WARNING)
            page.update()
            return

        registro_count = 0

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                # Reporte de Ventas
                if tipo == "Ventas":
                    columns = [
                        ft.DataColumn(ft.Text("ID", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Cliente", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Monto Total", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Fecha", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Detalle", color=Colors.PRIMARY)),
                    ]
                    tabla.columns.extend(columns)

                    query = """SELECT v.id, c.nombre, v.total, v.fecha_venta
                              FROM ventas v LEFT JOIN clientes c ON v.cliente_id = c.id WHERE 1=1"""
                    params = []
                    if fecha_ini:
                        query += " AND v.fecha_venta >= %s"
                        params.append(fecha_ini)
                    if fecha_fin:
                        query += " AND v.fecha_venta <= %s"
                        params.append(fecha_fin)
                    if filtro_texto:
                        query += " AND LOWER(c.nombre) LIKE %s"
                        params.append(f"%{filtro_texto}%")
                    query += " ORDER BY v.fecha_venta DESC LIMIT 100"

                    cur.execute(query, params)
                    for v in cur.fetchall():
                        registro_count += 1
                        tabla.rows.append(ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(v[0]))),
                            ft.DataCell(ft.Text(v[1] or "Sin cliente")),
                            ft.DataCell(ft.Text(format_guarani(v[2]))),
                            ft.DataCell(ft.Text(str(v[3])[:19] if v[3] else "")),
                            ft.DataCell(ft.IconButton(
                                icon=ft.icons.VISIBILITY,
                                icon_color=Colors.INFO,
                                tooltip="Ver detalle de venta",
                                on_click=lambda e, vid=v[0]: abrir_detalle_ventas(vid)
                            )),
                        ]))

                # Reporte de Pedidos
                elif tipo == "Pedidos":
                    columns = [
                        ft.DataColumn(ft.Text("ID", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Cliente", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Destino", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Estado", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Fecha", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Total", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("WhatsApp", color=Colors.PRIMARY)),
                    ]
                    tabla.columns.extend(columns)

                    query = """SELECT p.id, c.nombre, p.destino, p.estado, p.fecha_pedido,
                                     COALESCE(p.costo_total, 0) as total, c.telefono
                              FROM pedidos p
                              LEFT JOIN clientes c ON p.cliente_id = c.id
                              WHERE 1=1"""
                    params = []
                    if fecha_ini:
                        query += " AND p.fecha_pedido >= %s"
                        params.append(fecha_ini)
                    if fecha_fin:
                        query += " AND p.fecha_pedido <= %s"
                        params.append(fecha_fin)
                    if filtro_texto:
                        query += " AND (LOWER(c.nombre) LIKE %s OR LOWER(p.destino) LIKE %s)"
                        params.extend([f"%{filtro_texto}%", f"%{filtro_texto}%"])
                    query += " ORDER BY p.fecha_pedido DESC LIMIT 100"

                    cur.execute(query, params)
                    for p in cur.fetchall():
                        registro_count += 1
                        estado_color = Colors.ERROR if p[3] == "Pendiente" else Colors.SUCCESS if p[3] == "Entregado" else Colors.WARNING
                        estado_container = ft.Container(
                            content=ft.Text(p[3], color=Colors.TEXT_WHITE, weight="bold", size=FontSizes.SMALL),
                            bgcolor=estado_color,
                            padding=ft.padding.symmetric(vertical=4, horizontal=8),
                            border_radius=8
                        )

                        def crear_handler_whatsapp(tel, nom):
                            def handler(e):
                                if open_whatsapp(tel, nom):
                                    show_snackbar(f"Abriendo WhatsApp de {nom}", Colors.SUCCESS)
                                else:
                                    show_snackbar(Messages.WARNING_INVALID_PHONE, Colors.WARNING)
                            return handler

                        tabla.rows.append(ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(p[0]))),
                            ft.DataCell(ft.Text(p[1] or "Sin cliente")),
                            ft.DataCell(ft.Text(p[2] or "")),
                            ft.DataCell(estado_container),
                            ft.DataCell(ft.Text(str(p[4])[:19] if p[4] else "")),
                            ft.DataCell(ft.Text(format_guarani(p[5]))),
                            ft.DataCell(ft.IconButton(
                                icon=ft.icons.CHAT,
                                icon_color="#25D366",
                                tooltip="Contactar por WhatsApp",
                                on_click=crear_handler_whatsapp(p[6], p[1])
                            )),
                        ]))

                # Reporte de Clientes
                elif tipo == "Clientes":
                    columns = [
                        ft.DataColumn(ft.Text("ID", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Nombre", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("RUC", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Ciudad", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Total Compras", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("WhatsApp", color=Colors.PRIMARY)),
                    ]
                    tabla.columns.extend(columns)

                    query = """SELECT c.id, c.nombre, c.ruc, c.ciudad, c.telefono,
                                     COALESCE(SUM(v.total), 0) AS total_compras
                              FROM clientes c
                              LEFT JOIN ventas v ON c.id = v.cliente_id
                              WHERE 1=1"""
                    params = []
                    if fecha_ini:
                        query += " AND (v.fecha_venta >= %s OR v.fecha_venta IS NULL)"
                        params.append(fecha_ini)
                    if fecha_fin:
                        query += " AND (v.fecha_venta <= %s OR v.fecha_venta IS NULL)"
                        params.append(fecha_fin)
                    if filtro_texto:
                        query += " AND (LOWER(c.nombre) LIKE %s OR LOWER(c.ciudad) LIKE %s)"
                        params.extend([f"%{filtro_texto}%", f"%{filtro_texto}%"])

                    query += " GROUP BY c.id, c.nombre, c.ruc, c.ciudad, c.telefono ORDER BY total_compras DESC LIMIT 100"
                    cur.execute(query, params)

                    for c in cur.fetchall():
                        registro_count += 1

                        def crear_handler_whatsapp_cliente(tel, nom):
                            def handler(e):
                                if open_whatsapp(tel, nom):
                                    show_snackbar(f"Abriendo WhatsApp de {nom}", Colors.SUCCESS)
                                else:
                                    show_snackbar(Messages.WARNING_INVALID_PHONE, Colors.WARNING)
                            return handler

                        tabla.rows.append(ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(c[0]))),
                            ft.DataCell(ft.Text(c[1] or "")),
                            ft.DataCell(ft.Text(c[2] or "")),
                            ft.DataCell(ft.Text(c[3] or "")),
                            ft.DataCell(ft.Text(format_guarani(c[5]))),
                            ft.DataCell(ft.IconButton(
                                icon=ft.icons.CHAT,
                                icon_color="#25D366",
                                tooltip="Contactar por WhatsApp",
                                on_click=crear_handler_whatsapp_cliente(c[4], c[1])
                            )),
                        ]))

                # Reporte de Productos
                elif tipo == "Productos":
                    columns = [
                        ft.DataColumn(ft.Text("ID", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Nombre", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Categoría", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Precio Venta", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Stock", color=Colors.PRIMARY)),
                    ]
                    tabla.columns.extend(columns)

                    query = """SELECT id, nombre, categoria,
                                     COALESCE(precio_venta, precio, 0) as precio_final,
                                     COALESCE(stock, 0) as stock_final
                              FROM productos WHERE 1=1"""
                    params = []
                    if filtro_texto:
                        query += " AND (LOWER(nombre) LIKE %s OR LOWER(categoria) LIKE %s)"
                        params.extend([f"%{filtro_texto}%", f"%{filtro_texto}%"])
                    query += " ORDER BY nombre ASC LIMIT 100"

                    cur.execute(query, params)
                    for prod in cur.fetchall():
                        registro_count += 1
                        stock_final = prod[4]
                        stock_color = Colors.ERROR if stock_final <= 5 else Colors.WARNING if stock_final <= 10 else Colors.SUCCESS
                        stock_container = ft.Container(
                            content=ft.Text(str(stock_final), color=Colors.TEXT_WHITE, weight="bold", size=FontSizes.SMALL),
                            bgcolor=stock_color,
                            padding=ft.padding.symmetric(vertical=4, horizontal=8),
                            border_radius=8
                        )
                        tabla.rows.append(ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(prod[0]))),
                            ft.DataCell(ft.Text(prod[1] or "")),
                            ft.DataCell(ft.Text(prod[2] or "")),
                            ft.DataCell(ft.Text(format_guarani(prod[3]))),
                            ft.DataCell(stock_container),
                        ]))

                # Stock Mínimo
                elif tipo == "Stock Mínimo":
                    columns = [
                        ft.DataColumn(ft.Text("ID", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Producto", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Stock Actual", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Stock Mínimo", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Estado", color=Colors.PRIMARY)),
                    ]
                    tabla.columns.extend(columns)

                    query = """SELECT id, nombre, COALESCE(stock, 0) as stock_actual,
                                     COALESCE(stock_minimo, 5) as stock_min
                              FROM productos
                              WHERE COALESCE(stock, 0) <= COALESCE(stock_minimo, 5)"""
                    params = []
                    if filtro_texto:
                        query += " AND LOWER(nombre) LIKE %s"
                        params.append(f"%{filtro_texto}%")
                    query += " ORDER BY stock_actual ASC LIMIT 100"

                    cur.execute(query, params)
                    for prod in cur.fetchall():
                        registro_count += 1
                        stock_actual, stock_min = prod[2], prod[3]

                        if stock_actual == 0:
                            estado, color = "AGOTADO", Colors.ERROR
                        elif stock_actual <= stock_min * 0.5:
                            estado, color = "CRÍTICO", "#FF5722"
                        else:
                            estado, color = "BAJO", Colors.WARNING

                        estado_container = ft.Container(
                            content=ft.Text(estado, color=Colors.TEXT_WHITE, weight="bold", size=FontSizes.XSMALL),
                            bgcolor=color,
                            padding=ft.padding.symmetric(vertical=4, horizontal=8),
                            border_radius=8
                        )

                        tabla.rows.append(ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(prod[0]))),
                            ft.DataCell(ft.Text(prod[1] or "")),
                            ft.DataCell(ft.Text(str(stock_actual))),
                            ft.DataCell(ft.Text(str(stock_min))),
                            ft.DataCell(estado_container),
                        ]))

                # Productos Más Vendidos
                elif tipo == "Productos Más Vendidos":
                    columns = [
                        ft.DataColumn(ft.Text("Pos.", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Producto", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Cantidad", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Ingresos", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Categoría", color=Colors.PRIMARY)),
                    ]
                    tabla.columns.extend(columns)

                    query = """SELECT p.nombre, p.categoria, SUM(dv.cantidad) as total_vendido,
                                     SUM(dv.subtotal) as ingresos_totales
                              FROM detalle_ventas dv
                              JOIN productos p ON dv.producto_id = p.id
                              JOIN ventas v ON dv.venta_id = v.id
                              WHERE 1=1"""
                    params = []
                    if fecha_ini:
                        query += " AND v.fecha_venta >= %s"
                        params.append(fecha_ini)
                    if fecha_fin:
                        query += " AND v.fecha_venta <= %s"
                        params.append(fecha_fin)
                    if filtro_texto:
                        query += " AND LOWER(p.nombre) LIKE %s"
                        params.append(f"%{filtro_texto}%")
                    query += " GROUP BY p.id, p.nombre, p.categoria ORDER BY total_vendido DESC LIMIT 20"

                    cur.execute(query, params)
                    posicion = 1
                    for prod in cur.fetchall():
                        registro_count += 1
                        posicion_container = ft.Container(
                            content=ft.Text(f"#{posicion}", color=Colors.TEXT_WHITE, weight="bold"),
                            bgcolor=Colors.PRIMARY if posicion <= 3 else "#757575",
                            padding=ft.padding.symmetric(vertical=4, horizontal=8),
                            border_radius=8
                        )
                        tabla.rows.append(ft.DataRow(cells=[
                            ft.DataCell(posicion_container),
                            ft.DataCell(ft.Text(prod[0] or "")),
                            ft.DataCell(ft.Text(f"{prod[2]:,.0f}")),
                            ft.DataCell(ft.Text(format_guarani(prod[3]))),
                            ft.DataCell(ft.Text(prod[1] or "")),
                        ]))
                        posicion += 1

                # Clientes Frecuentes
                elif tipo == "Clientes Frecuentes":
                    columns = [
                        ft.DataColumn(ft.Text("Pos.", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Cliente", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Compras", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Total", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("Última Compra", color=Colors.PRIMARY)),
                        ft.DataColumn(ft.Text("WhatsApp", color=Colors.PRIMARY)),
                    ]
                    tabla.columns.extend(columns)

                    query = """SELECT c.nombre, c.telefono, COUNT(v.id) as total_compras,
                                     SUM(v.total) as total_gastado, MAX(v.fecha_venta) as ultima_compra
                              FROM clientes c
                              JOIN ventas v ON c.id = v.cliente_id
                              WHERE 1=1"""
                    params = []
                    if fecha_ini:
                        query += " AND v.fecha_venta >= %s"
                        params.append(fecha_ini)
                    if fecha_fin:
                        query += " AND v.fecha_venta <= %s"
                        params.append(fecha_fin)
                    if filtro_texto:
                        query += " AND LOWER(c.nombre) LIKE %s"
                        params.append(f"%{filtro_texto}%")
                    query += " GROUP BY c.id, c.nombre, c.telefono ORDER BY total_compras DESC, total_gastado DESC LIMIT 15"

                    cur.execute(query, params)
                    posicion = 1
                    for cliente in cur.fetchall():
                        registro_count += 1
                        posicion_container = ft.Container(
                            content=ft.Text(f"#{posicion}", color=Colors.TEXT_WHITE, weight="bold"),
                            bgcolor=Colors.PRIMARY if posicion <= 5 else "#757575",
                            padding=ft.padding.symmetric(vertical=4, horizontal=8),
                            border_radius=8
                        )

                        def crear_handler_whatsapp_freq(tel, nom):
                            def handler(e):
                                if open_whatsapp(tel, nom):
                                    show_snackbar(f"Abriendo WhatsApp de {nom}", Colors.SUCCESS)
                                else:
                                    show_snackbar(Messages.WARNING_INVALID_PHONE, Colors.WARNING)
                            return handler

                        tabla.rows.append(ft.DataRow(cells=[
                            ft.DataCell(posicion_container),
                            ft.DataCell(ft.Text(cliente[0] or "")),
                            ft.DataCell(ft.Text(f"{cliente[2]}")),
                            ft.DataCell(ft.Text(format_guarani(cliente[3]))),
                            ft.DataCell(ft.Text(str(cliente[4])[:19] if cliente[4] else "")),
                            ft.DataCell(ft.IconButton(
                                icon=ft.icons.CHAT,
                                icon_color="#25D366",
                                tooltip="Contactar por WhatsApp",
                                on_click=crear_handler_whatsapp_freq(cliente[1], cliente[0])
                            )),
                        ]))
                        posicion += 1

        except Exception as ex:
            error_msg.value = f"⚠️ Error al generar reporte: {str(ex)}"
            if not silent_mode:
                show_snackbar(f"Error: {str(ex)}", Colors.ERROR)
            print(f"Error en reporte: {ex}")

        # Actualizar contador de registros
        total_registros.value = f"📊 Total de registros: {registro_count}"

        if not silent_mode and registro_count > 0:
            show_snackbar(f"✅ Reporte generado: {registro_count} registros encontrados", Colors.PRIMARY)

        page.update()

    # UI de filtros y acciones
    filtros_card = ft.Container(
        content=ft.Column([
            ft.Text("🔍 Filtros de Búsqueda:", weight="bold", color=Colors.PRIMARY, size=FontSizes.NORMAL),
            ft.Row([
                filtro_tipo,
                fecha_ini_row,
                fecha_fin_row,
                filtro_adicional,
            ], spacing=Spacing.NORMAL, wrap=True),
            ft.Row([
                ft.ElevatedButton(
                    "🔍 Buscar",
                    bgcolor=Colors.PRIMARY,
                    color=Colors.TEXT_WHITE,
                    on_click=refrescar_tabla
                ),
                ft.ElevatedButton(
                    "📄 Exportar PDF",
                    bgcolor="#D32F2F",
                    color=Colors.TEXT_WHITE,
                    on_click=exportar_pdf,
                    tooltip="Exportar reporte a PDF"
                ),
                ft.ElevatedButton(
                    "🔄 Limpiar Filtros",
                    bgcolor="#757575",
                    color=Colors.TEXT_WHITE,
                    on_click=lambda e: limpiar_filtros()
                ),
            ], spacing=Spacing.NORMAL),
            total_registros,
        ], spacing=Spacing.NORMAL),
        padding=Spacing.LARGE,
        border_radius=Sizes.CARD_RADIUS,
        bgcolor=ft.colors.with_opacity(0.6, Colors.BG_WHITE),
        shadow=ft.BoxShadow(blur_radius=10, color="#CCC"),
    )

    def limpiar_filtros():
        filtro_fecha_ini.value = fecha_inicio_mes
        filtro_fecha_fin.value = fecha_actual
        filtro_adicional.value = ""
        filtro_tipo.value = "Ventas"
        refrescar_tabla()

    # Vista principal con scroll en la tabla
    tabla_card = ft.Container(
        content=ft.Column([
            filtros_card,
            error_msg,
            ft.Container(
                content=ft.Column(
                    [tabla],
                    scroll=ft.ScrollMode.AUTO,
                ),
                height=400,
                border=ft.border.all(1, Colors.BORDER_LIGHT),
                border_radius=Sizes.CARD_RADIUS,
                padding=Spacing.NORMAL,
            ),
        ], expand=True, spacing=Spacing.MEDIUM),
        expand=True,
        padding=Spacing.LARGE,
        border_radius=Sizes.CARD_RADIUS,
        bgcolor=Colors.CARD_BG,
        shadow=ft.BoxShadow(blur_radius=12, color="#444"),
        width=950,
    )

    volver_icon = ft.IconButton(
        icon=ft.icons.ARROW_BACK,
        tooltip="Volver al Dashboard",
        icon_color=Colors.PRIMARY,
        on_click=lambda e: dashboard.dashboard_view(content, page=page),
    )

    titulo = ft.Text("📊 Reportes y Análisis", size=FontSizes.XLARGE, weight="bold", color=Colors.PRIMARY)

    content.controls.append(
        ft.Column(
            [
                ft.Row([volver_icon, titulo], alignment=ft.MainAxisAlignment.START, spacing=Spacing.LARGE),
                tabla_card,
            ],
            expand=True,
            spacing=Spacing.LARGE,
        )
    )

    # Cargar reporte inicial
    refrescar_tabla()

    if page:
        page.update()

    print("✅ Módulo de Reportes cargado (PostgreSQL + Nueva Arquitectura)")
