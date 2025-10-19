from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import os
from datetime import datetime

# Configuración del documento
FACTURA_WIDTH = 210 * mm   # A4 ancho
FACTURA_HEIGHT = 297 * mm  # A4 alto

# Colores en blanco y negro
WHITE = colors.white
BLACK = colors.black
LIGHT_GREY = colors.HexColor("#F5F5F5")    # Gris muy claro para fondos
GREY = colors.HexColor("#E0E0E0")          # Gris para bordes
DARK_GREY = colors.HexColor("#757575")     # Gris oscuro para texto secundario

def formatear_guaranies(monto):
    """Formatea monto en guaraníes con 'Gs.' en lugar de ₲"""
    return f"Gs. {int(monto):,.0f}".replace(',', '.')

def generar_ticket_pdf(numero_venta, cliente_datos, carrito_items, totales_info, operador):
    """Genera un PDF en formato limpio blanco y negro con guaraníes"""
    
    # Crear directorio si no existe
    if not os.path.exists("tickets"):
        os.makedirs("tickets")
        print("📁 Directorio 'tickets' creado")
    
    filename = f"tickets/factura_{numero_venta}.pdf"
    
    try:
        print(f"📋 Generando factura limpia: {filename}")
        
        # Crear documento
        doc = SimpleDocTemplate(
            filename, 
            pagesize=(FACTURA_WIDTH, FACTURA_HEIGHT),
            rightMargin=15*mm, 
            leftMargin=15*mm, 
            topMargin=15*mm, 
            bottomMargin=20*mm
        )
        
        elementos = []
        
        # === ENCABEZADO PRINCIPAL SIN "Lista" ===
        titulo_data = [['Vivero Rocío', 'Vivero Rocío']]
        titulo_table = Table(titulo_data, colWidths=[90*mm, 90*mm])
        titulo_table.setStyle(TableStyle([
            # Celda izquierda - Título sin "Lista"
            ('BACKGROUND', (0, 0), (0, 0), WHITE),
            ('TEXTCOLOR', (0, 0), (0, 0), BLACK),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 18),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            
            # Celda derecha - Empresa
            ('BACKGROUND', (1, 0), (1, 0), WHITE),
            ('TEXTCOLOR', (1, 0), (1, 0), BLACK),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 16),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
            
            # Bordes y padding
            ('BOX', (0, 0), (-1, -1), 2, BLACK),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        elementos.append(titulo_table)
        elementos.append(Spacer(1, 5))
        
        # === INFORMACIÓN DEL DESTINATARIO Y DATOS ===
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        cliente_nombre = cliente_datos['nombre'] if cliente_datos else 'Cliente General'
        cliente_telefono = cliente_datos['telefono'] if cliente_datos and cliente_datos['telefono'] else 'N/A'
        
        info_data = [
            ['Destino', cliente_nombre[:40]],  # Aumentar longitud permitida
            ['Cel', cliente_telefono],
        ]
        
        info_table = Table(info_data, colWidths=[30*mm, 150*mm])
        info_table.setStyle(TableStyle([
            # Etiquetas (columna izquierda)
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GREY),
            ('TEXTCOLOR', (0, 0), (0, -1), BLACK),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            
            # Valores (columna derecha)
            ('BACKGROUND', (1, 0), (1, -1), WHITE),
            ('TEXTCOLOR', (1, 0), (1, -1), BLACK),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (1, 0), (1, -1), 12),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            
            # Bordes y padding
            ('GRID', (0, 0), (-1, -1), 1, GREY),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elementos.append(info_table)
        elementos.append(Spacer(1, 2))
        
        # === FILA DE FACTURA Y FECHA ===
        factura_fecha_data = [
            ['Factura', f'{operador} / {numero_venta}'],
            ['Fecha', fecha_actual],
        ]
        
        factura_fecha_table = Table(factura_fecha_data, colWidths=[30*mm, 150*mm])
        factura_fecha_table.setStyle(TableStyle([
            # Fila de Factura - con fondo gris
            ('BACKGROUND', (0, 0), (0, 0), LIGHT_GREY),
            ('BACKGROUND', (1, 0), (1, 0), GREY),
            ('TEXTCOLOR', (0, 0), (-1, 0), BLACK),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            
            # Fila de Fecha - fondo normal
            ('BACKGROUND', (0, 1), (0, 1), LIGHT_GREY),
            ('BACKGROUND', (1, 1), (1, 1), WHITE),
            ('TEXTCOLOR', (0, 1), (0, 1), BLACK),
            ('TEXTCOLOR', (1, 1), (1, 1), BLACK),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, 1), 'Helvetica'),
            
            # Configuración general
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Bordes y padding
            ('GRID', (0, 0), (-1, -1), 1, GREY),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elementos.append(factura_fecha_table)
        elementos.append(Spacer(1, 5))
        
        # === TABLA DE PRODUCTOS ===
        # Encabezado de la tabla de productos
        productos_header = [['Cantidad', 'Artículo', 'Precio Unitario', 'Total']]
        
        # Agregar productos con formato de guaraníes CORREGIDO
        productos_data = productos_header.copy()
        for item in carrito_items:
            productos_data.append([
                str(item['cantidad']),
                item['nombre'],
                formatear_guaranies(item['precio']),  # Usar función helper
                formatear_guaranies(item['cantidad'] * item['precio'])  # Usar función helper
            ])
        
        # Crear tabla de productos
        productos_table = Table(productos_data, colWidths=[25*mm, 85*mm, 35*mm, 35*mm])
        productos_table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), GREY),
            ('TEXTCOLOR', (0, 0), (-1, 0), BLACK),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Contenido de productos - filas alternadas
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            
            # Alineación por columnas
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),     # Cantidad centrada
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),       # Artículo izquierda
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),     # Precios derecha
            
            # Colores alternados para las filas de productos
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 1, GREY),
            ('LINEBELOW', (0, 0), (-1, 0), 2, BLACK),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elementos.append(productos_table)
        elementos.append(Spacer(1, 2))
        
        # === FILA DE DELIVERY/ENVÍO CORREGIDA ===
        delivery_data = [['', '', 'Delivery', 'Gs. 0']]  # CORREGIDO
        delivery_table = Table(delivery_data, colWidths=[25*mm, 85*mm, 35*mm, 35*mm])
        delivery_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GREY),
            ('TEXTCOLOR', (0, 0), (-1, -1), BLACK),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, GREY),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elementos.append(delivery_table)
        elementos.append(Spacer(1, 2))
        
        # === TOTAL FINAL CON GUARANÍES CORREGIDO ===
        total_final = totales_info['total']
        total_data = [['', '', '', formatear_guaranies(total_final)]]  # CORREGIDO
        total_table = Table(total_data, colWidths=[25*mm, 85*mm, 35*mm, 35*mm])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), GREY),
            ('TEXTCOLOR', (0, 0), (-1, -1), BLACK),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, BLACK),
            ('LINEABOVE', (0, 0), (-1, -1), 2, BLACK),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elementos.append(total_table)
        elementos.append(Spacer(1, 15))
        
        # === INFORMACIÓN DE PAGO CORREGIDA ===
        pago_info_data = [
            ['INFORMACIÓN DE PAGO'],
            [f'Método: {totales_info["metodo_pago"]}'],
            [f'Monto Recibido: {formatear_guaranies(totales_info["monto_pagado"])}'],  # CORREGIDO
            [f'Vuelto: {formatear_guaranies(totales_info["vuelto"])}'],  # CORREGIDO
        ]
        
        pago_info_table = Table(pago_info_data, colWidths=[180*mm])
        pago_info_table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (0, 0), BLACK),
            ('TEXTCOLOR', (0, 0), (0, 0), WHITE),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 12),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            
            # Contenido
            ('BACKGROUND', (0, 1), (0, -1), LIGHT_GREY),
            ('TEXTCOLOR', (0, 1), (0, -1), BLACK),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (0, -1), 11),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            # Bordes y padding
            ('GRID', (0, 0), (-1, -1), 1, GREY),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elementos.append(pago_info_table)
        elementos.append(Spacer(1, 20))
        
        # === PIE DE PÁGINA ===
        pie_data = [
            ['¡GRACIAS POR SU COMPRA!'],
            ['Vivero Rocío - Sistema de Gestión'],
            [f'Generado el {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'],
        ]
        
        pie_table = Table(pie_data, colWidths=[180*mm])
        pie_table.setStyle(TableStyle([
            # Primera fila - Agradecimiento
            ('BACKGROUND', (0, 0), (0, 0), BLACK),
            ('TEXTCOLOR', (0, 0), (0, 0), WHITE),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 14),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            
            # Resto de filas
            ('BACKGROUND', (0, 1), (0, -1), WHITE),
            ('TEXTCOLOR', (0, 1), (0, -1), DARK_GREY),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (0, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            
            # Bordes y padding
            ('BOX', (0, 0), (-1, -1), 1, GREY),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elementos.append(pie_table)
        
        # === GENERAR PDF ===
        doc.build(elementos)
        
        print(f"✅ Factura limpia generada: {filename}")
        
        # Verificar que el archivo se creó
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"📄 Archivo creado: {filename} ({file_size} bytes)")
            return filename
        else:
            print(f"❌ Error: El archivo no se creó: {filename}")
            return None
            
    except Exception as e:
        print(f"❌ Error generando factura: {e}")
        import traceback
        traceback.print_exc()
        return None

def abrir_pdf(archivo_pdf):
    """Abre el PDF con la aplicación predeterminada del sistema"""
    try:
        print(f"📖 Intentando abrir factura: {archivo_pdf}")
        
        if not os.path.exists(archivo_pdf):
            print(f"❌ Archivo no encontrado: {archivo_pdf}")
            return False
        
        ruta_absoluta = os.path.abspath(archivo_pdf)
        print(f"📂 Ruta absoluta: {ruta_absoluta}")
        
        import platform
        import subprocess
        
        sistema = platform.system()
        print(f"💻 Sistema operativo: {sistema}")
        
        try:
            if sistema == "Windows":
                subprocess.Popen(['cmd', '/c', 'start', '', ruta_absoluta], shell=True)
                print("✅ Factura abierta en Windows")
                return True
            elif sistema == "Darwin":  # macOS
                subprocess.Popen(['open', ruta_absoluta])
                print("✅ Factura abierta en macOS")
                return True
            else:  # Linux
                subprocess.Popen(['xdg-open', ruta_absoluta])
                print("✅ Factura abierta en Linux")
                return True
                
        except Exception as e:
            print(f"⚠️ Método principal falló: {e}")
            
            if sistema == "Windows":
                try:
                    os.startfile(ruta_absoluta)
                    print("✅ Factura abierta con método alternativo")
                    return True
                except Exception as e2:
                    print(f"❌ Método alternativo falló: {e2}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error crítico abriendo factura: {e}")
        return False