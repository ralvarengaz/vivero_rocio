import flet as ft
import sqlite3
import webbrowser
from modules import dashboard
from datetime import datetime, date
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

DB = "data/vivero.db"
PRIMARY_COLOR = "#2E7D32"
ACCENT_COLOR = "#66BB6A"

def crud_view(content, page=None):
    content.controls.clear()

    # --- Barra de mensajes
    def show_snackbar(msg, color):
        page.open(ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color, duration=3000))

    # --- Variables de fecha ---
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    fecha_inicio_mes = datetime.now().strftime("%Y-%m-01")
    
    # --- Campos de fecha con calendario ---
    filtro_fecha_ini = ft.TextField(
        label="Desde", 
        width=140, 
        prefix_icon=ft.Icons.DATE_RANGE,
        value=fecha_inicio_mes,
        on_change=lambda e: refrescar_tabla_auto(),
    )
    
    filtro_fecha_fin = ft.TextField(
        label="Hasta", 
        width=140, 
        prefix_icon=ft.Icons.DATE_RANGE,
        value=fecha_actual,
        on_change=lambda e: refrescar_tabla_auto(),
    )

    # --- DatePickers corregidos ---
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

    # Agregar los date pickers a la página
    page.overlay.extend([date_picker_ini, date_picker_fin])

    def abrir_calendario_ini(e):
        date_picker_ini.open = True
        page.update()

    def abrir_calendario_fin(e):
        date_picker_fin.open = True
        page.update()

    # --- Botones de calendario ---
    btn_calendario_ini = ft.IconButton(
        icon=ft.Icons.CALENDAR_TODAY,
        icon_color=PRIMARY_COLOR,
        tooltip="Seleccionar fecha inicial",
        on_click=abrir_calendario_ini,
    )
    
    btn_calendario_fin = ft.IconButton(
        icon=ft.Icons.CALENDAR_TODAY,
        icon_color=PRIMARY_COLOR,
        tooltip="Seleccionar fecha final",
        on_click=abrir_calendario_fin,
    )

    # --- Row para fechas con calendarios ---
    fecha_ini_row = ft.Row([filtro_fecha_ini, btn_calendario_ini], spacing=5)
    fecha_fin_row = ft.Row([filtro_fecha_fin, btn_calendario_fin], spacing=5)

    # --- Otros filtros ---
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
        prefix_icon=ft.Icons.SEARCH,
        hint_text="Nombre de cliente o producto",
        on_change=lambda e: refrescar_tabla_auto()
    )

    # --- Estado de tabla y mensajes ---
    tabla = ft.DataTable(
        columns=[],
        rows=[],
        column_spacing=10,
    )
    error_msg = ft.Text("", color="red")
    total_registros = ft.Text("", size=14, color=PRIMARY_COLOR)

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
            show_snackbar("⚠️ No hay datos en la tabla para exportar.", "#FFA000")
            return
        
        try:
            # Crear directorio de reportes si no existe
            if not os.path.exists("reportes"):
                os.makedirs("reportes")
                
            tipo = filtro_tipo.value
            fecha_reporte = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reportes/Reporte_{tipo.replace(' ', '_')}_{fecha_reporte}.pdf"
            
            # Crear el documento PDF
            doc = SimpleDocTemplate(filename, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Título del reporte
            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                textColor=colors.HexColor(PRIMARY_COLOR),
                alignment=1  # Centrado
            )
            
            story.append(Paragraph(f"REPORTE DE {tipo.upper()}", titulo_style))
            story.append(Paragraph(f"Vivero Rocío", styles['Heading2']))
            story.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
            story.append(Paragraph(f"Usuario: ralvarengazz", styles['Normal']))
            
            # Información de filtros
            if filtro_fecha_ini.value or filtro_fecha_fin.value:
                filtros_text = f"Período: {filtro_fecha_ini.value or 'Sin límite'} hasta {filtro_fecha_fin.value or 'Sin límite'}"
                story.append(Paragraph(filtros_text, styles['Normal']))
            
            if filtro_adicional.value:
                story.append(Paragraph(f"Filtro adicional: {filtro_adicional.value}", styles['Normal']))
                
            story.append(Spacer(1, 20))
            
            # Preparar datos de la tabla - CORREGIDO
            headers = []
            for col in tabla.columns:
                # Corregir: usar 'label' en lugar de 'content'
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
                        # Para TextField, Text, etc.
                        cell_text = str(cell.content.value)
                    elif hasattr(cell.content, 'content'):
                        # Para Container con contenido
                        if hasattr(cell.content.content, 'value'):
                            cell_text = str(cell.content.content.value)
                        else:
                            cell_text = "Estado"
                    elif hasattr(cell.content, 'icon'):
                        # Para IconButton
                        cell_text = "Acción"
                    elif hasattr(cell.content, 'text'):
                        # Para otros controles con texto
                        cell_text = str(cell.content.text)
                    
                    # Limpiar formato monetario para PDF
                    if cell_text.startswith("₲"):
                        cell_text = cell_text.replace("₲", "Gs. ")
                    
                    row_data.append(cell_text)
                data.append(row_data)
            
            # Crear la tabla en PDF
            if data and len(data) > 1:  # Verificar que hay datos
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(PRIMARY_COLOR)),
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
            
            # Resumen al final
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Total de registros: {len(tabla.rows)}", styles['Normal']))
            
            # Generar el PDF
            doc.build(story)
            
            show_snackbar(f"📄 PDF generado exitosamente: {os.path.basename(filename)}", PRIMARY_COLOR)
            
            # Intentar abrir el archivo
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
                        show_snackbar(f"📁 Archivo guardado en: {filename}", "#0288D1")
                        
        except Exception as ex:
            show_snackbar(f"❌ Error al generar PDF: {str(ex)}", "#F44336")
            print(f"Error detallado: {ex}")

    def refrescar_tabla_auto():
        refrescar_tabla(silent_mode=True)

    def abrir_detalle_ventas(venta_id):
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("""
            SELECT p.nombre, dv.cantidad, dv.precio_unitario, dv.subtotal 
            FROM detalle_ventas dv 
            JOIN productos p ON dv.producto_id = p.id 
            WHERE dv.venta_id = ?
        """, (venta_id,))
        detalles = cur.fetchall()
        conn.close()
        
        if detalles:
            detalle_text = f"Detalle Venta #{venta_id}:\n"
            for d in detalles:
                detalle_text += f"• {d[0]} - Cant: {d[1]} - Precio: ₲{d[2]:,.0f} - Subtotal: ₲{d[3]:,.0f}\n"
            show_snackbar(detalle_text, "#0288D1")
        else:
            show_snackbar(f"No se encontraron detalles para la venta #{venta_id}", "#FFA000")

    def contactar_cliente_whatsapp(telefono, nombre):
        if telefono:
            num = telefono.strip()
            if num.startswith("0"):
                num = "595" + num[1:]
            num = "".join(ch for ch in num if ch.isdigit())
            url = f"https://wa.me/{num}?text=Hola%20{nombre or 'cliente'}"
            webbrowser.open(url)
        else:
            show_snackbar("⚠️ Número no válido para WhatsApp.", "#FFA000")

    # --- Función principal para refrescar la tabla ---
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
                show_snackbar(error, "#FFA000")
            page.update()
            return
        
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        registro_count = 0

        try:
            # --- Reporte de Ventas ---
            if tipo == "Ventas":
                columns = [
                    ft.DataColumn(ft.Text("ID", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Cliente", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Monto Total", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Fecha", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Detalle", color=PRIMARY_COLOR)),
                ]
                tabla.columns.extend(columns)
                
                query = """SELECT v.id, c.nombre, v.total, v.fecha_venta 
                          FROM ventas v LEFT JOIN clientes c ON v.cliente_id = c.id WHERE 1=1"""
                params = []
                if fecha_ini:
                    query += " AND v.fecha_venta >= ?"
                    params.append(fecha_ini)
                if fecha_fin:
                    query += " AND v.fecha_venta <= ?"
                    params.append(fecha_fin)
                if filtro_texto:
                    query += " AND LOWER(c.nombre) LIKE ?"
                    params.append(f"%{filtro_texto}%")
                query += " ORDER BY v.fecha_venta DESC"
                
                cur.execute(query, params)
                for v in cur.fetchall():
                    registro_count += 1
                    tabla.rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(v[0]))),
                        ft.DataCell(ft.Text(v[1] or "Sin cliente")),
                        ft.DataCell(ft.Text(f"₲ {v[2]:,.0f}")),
                        ft.DataCell(ft.Text(v[3])),
                        ft.DataCell(ft.IconButton(
                            icon=ft.Icons.VISIBILITY,
                            icon_color="#0288D1",
                            tooltip="Ver detalle de venta",
                            on_click=lambda e, vid=v[0]: abrir_detalle_ventas(vid)
                        )),
                    ]))

            # --- Reporte de Pedidos ---
            elif tipo == "Pedidos":
                columns = [
                    ft.DataColumn(ft.Text("ID", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Cliente", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Destino", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Estado", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Fecha", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Total", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("WhatsApp", color=PRIMARY_COLOR)),
                ]
                tabla.columns.extend(columns)
                
                query = """SELECT p.id, c.nombre, p.destino, p.estado, p.fecha_pedido, 
                                 IFNULL(SUM(d.subtotal), 0) + IFNULL(p.costo_delivery, 0), c.telefono
                          FROM pedidos p 
                          LEFT JOIN clientes c ON p.cliente_id = c.id 
                          LEFT JOIN detalle_pedido d ON p.id = d.pedido_id
                          WHERE 1=1"""
                params = []
                if fecha_ini:
                    query += " AND p.fecha_pedido >= ?"
                    params.append(fecha_ini)
                if fecha_fin:
                    query += " AND p.fecha_pedido <= ?"
                    params.append(fecha_fin)
                if filtro_texto:
                    query += " AND (LOWER(c.nombre) LIKE ? OR LOWER(p.destino) LIKE ?)"
                    params.extend([f"%{filtro_texto}%", f"%{filtro_texto}%"])
                query += " GROUP BY p.id ORDER BY p.fecha_pedido DESC"
                
                cur.execute(query, params)
                for p in cur.fetchall():
                    registro_count += 1
                    estado_color = "#F44336" if p[3] == "Pendiente" else "#4CAF50" if p[3] == "Entregado" else "#FF9800"
                    estado_container = ft.Container(
                        content=ft.Text(p[3], color="white", weight="bold", size=12),
                        bgcolor=estado_color,
                        padding=ft.padding.symmetric(vertical=4, horizontal=8),
                        border_radius=8
                    )
                    tabla.rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(p[0]))),
                        ft.DataCell(ft.Text(p[1] or "Sin cliente")),
                        ft.DataCell(ft.Text(p[2] or "")),
                        ft.DataCell(estado_container),
                        ft.DataCell(ft.Text(p[4])),
                        ft.DataCell(ft.Text(f"₲ {p[5]:,.0f}")),
                        ft.DataCell(ft.IconButton(
                            icon=ft.Icons.CHAT,
                            icon_color="#25D366",
                            tooltip="Contactar por WhatsApp",
                            on_click=lambda e, tel=p[6], nom=p[1]: contactar_cliente_whatsapp(tel, nom)
                        )),
                    ]))

            # --- Reporte de Clientes ---
            elif tipo == "Clientes":
                columns = [
                    ft.DataColumn(ft.Text("ID", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Nombre", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("RUC", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Ciudad", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Total Compras", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("WhatsApp", color=PRIMARY_COLOR)),
                ]
                tabla.columns.extend(columns)
                
                query = """SELECT c.id, c.nombre, c.ruc, c.ciudad, c.telefono, 
                                 IFNULL(SUM(v.total), 0) AS total_compras
                          FROM clientes c
                          LEFT JOIN ventas v ON c.id = v.cliente_id
                          WHERE 1=1"""
                params = []
                if fecha_ini:
                    query += " AND c.id IN (SELECT cliente_id FROM ventas WHERE fecha_venta >= ?)"
                    params.append(fecha_ini)
                if fecha_fin:
                    query += " AND c.id IN (SELECT cliente_id FROM ventas WHERE fecha_venta <= ?)"
                    params.append(fecha_fin)
                if filtro_texto:
                    query += " AND (LOWER(c.nombre) LIKE ? OR LOWER(c.ciudad) LIKE ?)"
                    params.extend([f"%{filtro_texto}%", f"%{filtro_texto}%"])
                
                query += " GROUP BY c.id ORDER BY total_compras DESC"
                cur.execute(query, params)
                for c in cur.fetchall():
                    registro_count += 1
                    tabla.rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(c[0]))),
                        ft.DataCell(ft.Text(c[1] or "")),
                        ft.DataCell(ft.Text(c[2] or "")),
                        ft.DataCell(ft.Text(c[3] or "")),
                        ft.DataCell(ft.Text(f"₲ {c[5]:,.0f}")),
                        ft.DataCell(ft.IconButton(
                            icon=ft.Icons.CHAT,
                            icon_color="#25D366",
                            tooltip="Contactar por WhatsApp",
                            on_click=lambda e, tel=c[4], nom=c[1]: contactar_cliente_whatsapp(tel, nom)
                        )),
                    ]))

            # --- Reporte de Productos ---
            elif tipo == "Productos":
                columns = [
                    ft.DataColumn(ft.Text("ID", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Nombre", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Categoría", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Precio Venta", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Stock", color=PRIMARY_COLOR)),
                ]
                tabla.columns.extend(columns)
                
                query = "SELECT id, nombre, categoria, precio_venta, IFNULL(stock_actual, 0) FROM productos WHERE 1=1"
                params = []
                if filtro_texto:
                    query += " AND (LOWER(nombre) LIKE ? OR LOWER(categoria) LIKE ?)"
                    params.extend([f"%{filtro_texto}%", f"%{filtro_texto}%"])
                query += " ORDER BY nombre ASC"
                
                cur.execute(query, params)
                for prod in cur.fetchall():
                    registro_count += 1
                    stock_color = "#F44336" if prod[4] <= 5 else "#FF9800" if prod[4] <= 10 else "#4CAF50"
                    stock_container = ft.Container(
                        content=ft.Text(str(prod[4]), color="white", weight="bold", size=12),
                        bgcolor=stock_color,
                        padding=ft.padding.symmetric(vertical=4, horizontal=8),
                        border_radius=8
                    )
                    tabla.rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(prod[0]))),
                        ft.DataCell(ft.Text(prod[1] or "")),
                        ft.DataCell(ft.Text(prod[2] or "")),
                        ft.DataCell(ft.Text(f"₲ {prod[3]:,.0f}")),
                        ft.DataCell(stock_container),
                    ]))

            # --- Stock Mínimo ---
            elif tipo == "Stock Mínimo":
                columns = [
                    ft.DataColumn(ft.Text("ID", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Producto", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Stock Actual", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Stock Mínimo", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Estado", color=PRIMARY_COLOR)),
                ]
                tabla.columns.extend(columns)
                
                query = """SELECT id, nombre, IFNULL(stock_actual, 0), IFNULL(stock_minimo, 5)
                          FROM productos 
                          WHERE IFNULL(stock_actual, 0) <= IFNULL(stock_minimo, 5)"""
                params = []
                if filtro_texto:
                    query += " AND LOWER(nombre) LIKE ?"
                    params.append(f"%{filtro_texto}%")
                query += " ORDER BY stock_actual ASC"
                
                cur.execute(query, params)
                for prod in cur.fetchall():
                    registro_count += 1
                    stock_actual, stock_min = prod[2], prod[3]
                    
                    if stock_actual == 0:
                        estado, color = "AGOTADO", "#F44336"
                    elif stock_actual <= stock_min * 0.5:
                        estado, color = "CRÍTICO", "#FF5722"
                    else:
                        estado, color = "BAJO", "#FF9800"
                    
                    estado_container = ft.Container(
                        content=ft.Text(estado, color="white", weight="bold", size=11),
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

            # --- Productos Más Vendidos ---
            elif tipo == "Productos Más Vendidos":
                columns = [
                    ft.DataColumn(ft.Text("Pos.", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Producto", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Cantidad", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Ingresos", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Categoría", color=PRIMARY_COLOR)),
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
                    query += " AND v.fecha_venta >= ?"
                    params.append(fecha_ini)
                if fecha_fin:
                    query += " AND v.fecha_venta <= ?"
                    params.append(fecha_fin)
                if filtro_texto:
                    query += " AND LOWER(p.nombre) LIKE ?"
                    params.append(f"%{filtro_texto}%")
                query += " GROUP BY p.id ORDER BY total_vendido DESC LIMIT 20"
                
                cur.execute(query, params)
                posicion = 1
                for prod in cur.fetchall():
                    registro_count += 1
                    posicion_container = ft.Container(
                        content=ft.Text(f"#{posicion}", color="white", weight="bold"),
                        bgcolor=PRIMARY_COLOR if posicion <= 3 else "#757575",
                        padding=ft.padding.symmetric(vertical=4, horizontal=8),
                        border_radius=8
                    )
                    tabla.rows.append(ft.DataRow(cells=[
                        ft.DataCell(posicion_container),
                        ft.DataCell(ft.Text(prod[0] or "")),
                        ft.DataCell(ft.Text(f"{prod[2]:,.0f}")),
                        ft.DataCell(ft.Text(f"₲ {prod[3]:,.0f}")),
                        ft.DataCell(ft.Text(prod[1] or "")),
                    ]))
                    posicion += 1

            # --- Clientes Frecuentes ---
            elif tipo == "Clientes Frecuentes":
                columns = [
                    ft.DataColumn(ft.Text("Pos.", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Cliente", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Compras", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Total", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("Última Compra", color=PRIMARY_COLOR)),
                    ft.DataColumn(ft.Text("WhatsApp", color=PRIMARY_COLOR)),
                ]
                tabla.columns.extend(columns)
                
                query = """SELECT c.nombre, c.telefono, COUNT(v.id) as total_compras, 
                                 SUM(v.total) as total_gastado, MAX(v.fecha_venta) as ultima_compra
                          FROM clientes c
                          JOIN ventas v ON c.id = v.cliente_id
                          WHERE 1=1"""
                params = []
                if fecha_ini:
                    query += " AND v.fecha_venta >= ?"
                    params.append(fecha_ini)
                if fecha_fin:
                    query += " AND v.fecha_venta <= ?"
                    params.append(fecha_fin)
                if filtro_texto:
                    query += " AND LOWER(c.nombre) LIKE ?"
                    params.append(f"%{filtro_texto}%")
                query += " GROUP BY c.id ORDER BY total_compras DESC, total_gastado DESC LIMIT 15"
                
                cur.execute(query, params)
                posicion = 1
                for cliente in cur.fetchall():
                    registro_count += 1
                    posicion_container = ft.Container(
                        content=ft.Text(f"#{posicion}", color="white", weight="bold"),
                        bgcolor=PRIMARY_COLOR if posicion <= 5 else "#757575",
                        padding=ft.padding.symmetric(vertical=4, horizontal=8),
                        border_radius=8
                    )
                    tabla.rows.append(ft.DataRow(cells=[
                        ft.DataCell(posicion_container),
                        ft.DataCell(ft.Text(cliente[0] or "")),
                        ft.DataCell(ft.Text(f"{cliente[2]}")),
                        ft.DataCell(ft.Text(f"₲ {cliente[3]:,.0f}")),
                        ft.DataCell(ft.Text(cliente[4] or "")),
                        ft.DataCell(ft.IconButton(
                            icon=ft.Icons.CHAT,
                            icon_color="#25D366",
                            tooltip="Contactar por WhatsApp",
                            on_click=lambda e, tel=cliente[1], nom=cliente[0]: contactar_cliente_whatsapp(tel, nom)
                        )),
                    ]))
                    posicion += 1

        except Exception as ex:
            error_msg.value = f"⚠️ Error al generar reporte: {str(ex)}"
            if not silent_mode:
                show_snackbar(f"Error: {str(ex)}", "#F44336")
        finally:
            conn.close()

        # Actualizar contador de registros
        total_registros.value = f"📊 Total de registros: {registro_count}"
        
        if not silent_mode and registro_count > 0:
            show_snackbar(f"✅ Reporte generado: {registro_count} registros encontrados", PRIMARY_COLOR)
        
        page.update()

    # --- UI de filtros y acciones ---
    filtros_card = ft.Container(
        content=ft.Column([
            ft.Text("🔍 Filtros de Búsqueda:", weight="bold", color=PRIMARY_COLOR, size=16),
            ft.Row([
                filtro_tipo,
                fecha_ini_row,
                fecha_fin_row,
                filtro_adicional,
            ], spacing=12, wrap=True),
            ft.Row([
                ft.ElevatedButton(
                    "🔍 Buscar", 
                    bgcolor=PRIMARY_COLOR, 
                    color="white", 
                    on_click=refrescar_tabla
                ),
                ft.ElevatedButton(
                    "📄 Exportar PDF", 
                    bgcolor="#D32F2F", 
                    color="white", 
                    on_click=exportar_pdf,
                    tooltip="Exportar reporte a PDF"
                ),
                ft.ElevatedButton(
                    "🔄 Limpiar Filtros", 
                    bgcolor="#757575", 
                    color="white", 
                    on_click=lambda e: limpiar_filtros()
                ),
            ], spacing=12),
            total_registros,
        ], spacing=10),
        padding=20,
        border_radius=15,
        bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
        shadow=ft.BoxShadow(blur_radius=10, color="#CCC"),
    )

    def limpiar_filtros():
        filtro_fecha_ini.value = fecha_inicio_mes
        filtro_fecha_fin.value = fecha_actual
        filtro_adicional.value = ""
        filtro_tipo.value = "Ventas"
        refrescar_tabla()

    # --- Vista principal con scroll en la tabla ---
    tabla_card = ft.Container(
        content=ft.Column([
            filtros_card,
            error_msg,
            ft.ListView(
                controls=[
                    ft.Row([tabla], expand=True, scroll=ft.ScrollMode.AUTO)
                ],
                expand=True,
                spacing=0,
                padding=0,
                height=400,
            ),
        ], expand=True),
        expand=True,
        padding=20,
        border_radius=20,
        bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        shadow=ft.BoxShadow(blur_radius=12, color="#444"),
        width=950,
    )

    volver_icon = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        tooltip="Volver al Dashboard",
        icon_color=PRIMARY_COLOR,
        on_click=lambda e: dashboard.dashboard_view(content, page=page),
    )

    titulo = ft.Text("📊 Reportes y Análisis", size=25, weight="bold", color=PRIMARY_COLOR)

    content.controls.append(
        ft.Column(
            [
                ft.Row([volver_icon, titulo], alignment=ft.MainAxisAlignment.START, spacing=20),
                tabla_card,
            ],
            expand=True,
            spacing=20,
        )
    )

    # Cargar reporte inicial
    refrescar_tabla()

    if page:
        page.update()