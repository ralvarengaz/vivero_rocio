import flet as ft
import re

# --- Normalización de moneda Gs. ---
def to_int(v):
    if isinstance(v, (int, float)): return int(v)
    if v is None: return 0
    s = str(v).strip()
    s = s.replace("Gs.", "").replace("Gs", "").replace("gs.", "").replace("gs", "")
    s = s.replace(".", "").replace(",", "")
    s = re.sub(r"\s+", "", s)
    return int(s) if s.isdigit() else 0

def format_gs(n):
    try:
        n = int(round(float(n)))
    except Exception:
        n = 0
    return f"{n:,}".replace(",", ".") + " Gs."

import sqlite3

# --- Helper: obtener precio_venta del producto ---
def get_precio_producto(conn, producto_id=None, nombre=None):
    cur = conn.cursor()
    if producto_id is not None:
        cur.execute("SELECT precio_venta FROM productos WHERE id=?", (producto_id,))
    else:
        cur.execute("SELECT precio_venta FROM productos WHERE nombre=?", (nombre,))
    row = cur.fetchone()
    return row[0] if row else 0

import time
import threading
from datetime import datetime
from contextlib import contextmanager
from session_manager import session
from pdf_generator import generar_ticket_pdf, abrir_pdf

DB = "data/vivero.db"
PRIMARY_COLOR = "#2E7D32"
ACCENT_COLOR = "#66BB6A"
SUCCESS_COLOR = "#4CAF50"
WARNING_COLOR = "#FF9800"
ERROR_COLOR = "#F44336"

# Lock global para la base de datos
db_lock = threading.Lock()

@contextmanager
def get_db_connection(timeout=30):
    """Context manager para manejo seguro de conexiones SQLite"""
    conn = None
    try:
        with db_lock:
            conn = sqlite3.connect(DB, timeout=timeout)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA cache_size=10000")
            yield conn
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print(f"⚠️ BD bloqueada, reintentando...")
            time.sleep(1)
            try:
                conn = sqlite3.connect(DB, timeout=timeout)
                conn.execute("PRAGMA journal_mode=WAL")
                yield conn
            except Exception as retry_error:
                print(f"❌ Error en reintento: {retry_error}")
                raise retry_error
        else:
            raise e
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

def crud_view(content, page=None):
    print("🛒 Iniciando módulo de ventas PdV COMPLETO...")
    
    # Limpiar contenido
    if hasattr(content, 'controls'):
        content.controls.clear()
    else:
        content.content = None
    
    # Verificar usuario
    current_user = session.get_current_user()
    if not current_user:
        print("❌ Usuario no encontrado")
        return
    
    # Verificar permisos
    puede_ver = session.tiene_permiso('ventas', 'ver')
    if not puede_ver:
        print("❌ Sin permisos para ver ventas")
        return

    # --- Variables globales del módulo ---
    sesion_actual = {"id": None, "monto_apertura": 0}
    carrito_venta = []
    modal_overlay = None
    actualizar_carrito_fn = None
    actualizar_ventas_fn = None
    
    print(f"👤 Usuario actual: {current_user['nombre_completo']} (ID: {current_user['id']})")
    
    # --- Función para volver al dashboard ---
    def volver_dashboard():
        """Regresa al dashboard principal"""
        try:
            from modules import dashboard
            print("🔙 Regresando al dashboard...")
            dashboard.dashboard_view(content, page=page)
        except Exception as e:
            print(f"❌ Error navegando al dashboard: {e}")
    
    # --- Funciones de base de datos MEJORADAS ---
    def obtener_sesion_activa():
        """Obtiene la sesión de caja activa del usuario"""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT sc.id, sc.monto_apertura, c.nombre, sc.fecha_apertura
                    FROM sesiones_caja sc
                    JOIN cajas c ON sc.caja_id = c.id
                    WHERE sc.usuario_id = ? AND sc.estado = 'Abierta'
                    ORDER BY sc.fecha_apertura DESC
                    LIMIT 1
                """, (current_user['id'],))
                result = cur.fetchone()
                return result
        except Exception as e:
            print(f"Error obteniendo sesión activa: {e}")
            return None

    def abrir_caja(monto_apertura):
        """Abre una nueva sesión de caja"""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Verificar sesión existente
                cur.execute("""
                    SELECT id FROM sesiones_caja 
                    WHERE usuario_id = ? AND estado = 'Abierta'
                """, (current_user['id'],))
                
                sesion_existente = cur.fetchone()
                if sesion_existente:
                    print(f"⚠️ Ya existe sesión abierta: {sesion_existente[0]}")
                    return sesion_existente[0]
                
                # Obtener o crear caja principal
                cur.execute("SELECT id FROM cajas WHERE nombre = 'Caja Principal'")
                caja_result = cur.fetchone()
                
                if not caja_result:
                    print("📦 Creando caja principal...")
                    cur.execute("""
                        INSERT INTO cajas (nombre, descripcion, creado_por)
                        VALUES ('Caja Principal', 'Caja principal del vivero', ?)
                    """, (current_user['id'],))
                    caja_id = cur.lastrowid
                    print(f"✅ Caja principal creada con ID: {caja_id}")
                else:
                    caja_id = caja_result[0]
                    print(f"📦 Usando caja existente ID: {caja_id}")
                
                # Crear nueva sesión
                cur.execute("""
                    INSERT INTO sesiones_caja (caja_id, usuario_id, monto_apertura, estado, fecha_apertura)
                    VALUES (?, ?, ?, 'Abierta', datetime('now', 'localtime'))
                """, (caja_id, current_user['id'], monto_apertura))
                
                sesion_id = cur.lastrowid
                conn.commit()
                
                print(f"✅ Caja abierta exitosamente - ID: {sesion_id}, Monto: ₲{monto_apertura:,}")
                return sesion_id
                
        except Exception as e:
            print(f"❌ Error abriendo caja: {e}")
            import traceback
            traceback.print_exc()
            return None

    def cerrar_caja(sesion_id, monto_cierre, observaciones=""):
        """Cierra la sesión de caja actual"""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Calcular total de ventas
                cur.execute("""
                    SELECT IFNULL(SUM(total), 0) FROM ventas 
                    WHERE sesion_caja_id = ?
                """, (sesion_id,))
                total_ventas = cur.fetchone()[0] or 0
                
                # Obtener monto de apertura
                cur.execute("SELECT monto_apertura FROM sesiones_caja WHERE id = ?", (sesion_id,))
                monto_apertura_result = cur.fetchone()
                monto_apertura = monto_apertura_result[0] if monto_apertura_result else 0
                
                # Calcular diferencia
                diferencia = monto_cierre - (monto_apertura + total_ventas)
                
                # Actualizar sesión
                cur.execute("""
                    UPDATE sesiones_caja 
                    SET fecha_cierre = datetime('now', 'localtime'),
                        monto_cierre = ?, total_ventas = ?, diferencia = ?,
                        estado = 'Cerrada', observaciones = ?
                    WHERE id = ?
                """, (monto_cierre, total_ventas, diferencia, observaciones, sesion_id))
                
                conn.commit()
                
                print(f"✅ Caja cerrada - ID: {sesion_id}, Cierre: ₲{monto_cierre:,}, Ventas: ₲{total_ventas:,}, Diferencia: ₲{diferencia:,}")
                return True
        except Exception as e:
            print(f"❌ Error cerrando caja: {e}")
            return False

    def obtener_productos():
        """Obtiene productos activos con stock"""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, nombre, categoria,
                           COALESCE(NULLIF(CAST(precio_venta AS INTEGER), 0),
                                    NULLIF(CAST(precio AS INTEGER), 0),
                                    0) AS precio_final,
                           COALESCE(stock, 0) AS stock_final,
                           COALESCE(unidad_medida, unidad, 'Unidad') AS unidad_final
                    FROM productos
                    WHERE COALESCE(stock, 0) >= 0
                    ORDER BY nombre
                """)
                productos = cur.fetchall()
                print(f"📦 Productos disponibles: {len(productos)}")
                return productos
        except Exception as e:
            print(f"Error obteniendo productos: {e}")
            return []

    def obtener_clientes():
        """Obtiene clientes activos"""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, nombre, 
                           COALESCE(telefono, '') as telefono,
                           COALESCE(email, correo, '') as email, 
                           COALESCE(direccion, ubicacion, '') as direccion
                    FROM clientes 
                    ORDER BY nombre
                """)
                clientes = cur.fetchall()
                print(f"👥 Clientes disponibles: {len(clientes)}")
                return clientes if clientes else [(1, "Cliente General", "", "", "")]
        except Exception as e:
            print(f"Error obteniendo clientes: {e}")
            return [(1, "Cliente General", "", "", "")]

    def obtener_cliente_por_id(cliente_id):
        """Obtiene datos completos del cliente por ID"""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, nombre, 
                           COALESCE(telefono, '') as telefono,
                           COALESCE(email, correo, '') as email,
                           COALESCE(direccion, ubicacion, '') as direccion
                    FROM clientes 
                    WHERE id = ?
                """, (cliente_id,))
                cliente = cur.fetchone()
                return cliente
        except Exception as e:
            print(f"Error obteniendo cliente {cliente_id}: {e}")
            return None

    def obtener_ventas_del_dia():
        """Obtiene las ventas del día actual"""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT COALESCE(v.numero_venta, 'V' || v.id) as numero, 
                           v.total, 
                           COALESCE(v.metodo_pago, 'Efectivo') as metodo, 
                           v.fecha_venta, 
                           COALESCE(c.nombre, 'Cliente General') as cliente_nombre,
                           COALESCE(u.nombre_completo, 'N/A') as vendedor
                    FROM ventas v
                    LEFT JOIN clientes c ON v.cliente_id = c.id
                    LEFT JOIN usuarios u ON v.usuario_id = u.id
                    WHERE DATE(v.fecha_venta) = DATE('now', 'localtime')
                    ORDER BY v.fecha_venta DESC
                    LIMIT 20
                """)
                ventas = cur.fetchall()
                return ventas
        except Exception as e:
            print(f"Error obteniendo ventas del día: {e}")
            return []

    def generar_numero_venta():
        """Genera número único de venta"""
        now = datetime.now()
        return f"V{now.strftime('%Y%m%d%H%M%S')}"

    def guardar_venta(cliente_id, subtotal, descuento, total, monto_pagado, vuelto, metodo_pago, carrito):
        """Guarda la venta completa con detalles - CON REINTENTOS"""
        max_reintentos = 3
        for intento in range(max_reintentos):
            try:
                print(f"💾 Intento {intento + 1} de {max_reintentos} - Guardando venta...")
                
                with get_db_connection(timeout=60) as conn:
                    cur = conn.cursor()
                    
                    # Iniciar transacción
                    conn.execute("BEGIN IMMEDIATE")
                    
                    numero_venta = generar_numero_venta()
                    print(f"💾 Guardando venta {numero_venta}...")
                    
                    # Insertar venta principal
                    cur.execute("""
                        INSERT INTO ventas (numero_venta, sesion_caja_id, cliente_id, usuario_id,
                                          total, subtotal, descuento, monto_pagado, vuelto, 
                                          metodo_pago, fecha_venta, estado)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), 'Completada')
                    """, (numero_venta, sesion_actual["id"], cliente_id, current_user['id'],
                          total, subtotal, descuento, monto_pagado, vuelto, metodo_pago))
                    
                    venta_id = cur.lastrowid
                    print(f"✅ Venta principal guardada con ID: {venta_id}")
                    
                    # Insertar detalles y actualizar stock
                    for i, item in enumerate(carrito, 1):
                        producto_id, cantidad, precio_unitario = item['id'], item['cantidad'], item['precio']
                        subtotal_item = cantidad * precio_unitario
                        
                        # Insertar detalle
                        cur.execute("""
                            INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                            VALUES (?, ?, ?, ?, ?)
                        """, (venta_id, producto_id, cantidad, precio_unitario, subtotal_item))
                        
                        # Actualizar stock
                        cur.execute("""
                            UPDATE productos SET stock = stock - ? WHERE id = ?
                        """, (cantidad, producto_id))
                        
                        print(f"  📋 Detalle {i}: {item['nombre']} x{cantidad} = ₲{subtotal_item:,}")
                    
                    # Confirmar transacción
                    conn.commit()
                    
                    print(f"🎉 Venta {numero_venta} guardada exitosamente - Total: ₲{total:,}")
                    return True, numero_venta
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and intento < max_reintentos - 1:
                    wait_time = (intento + 1) * 2
                    print(f"⚠️ BD bloqueada en intento {intento + 1}, esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Error de BD después de {intento + 1} intentos: {e}")
                    return False, str(e)
            except Exception as e:
                print(f"❌ Error inesperado guardando venta: {e}")
                import traceback
                traceback.print_exc()
                return False, str(e)
        
        print(f"❌ Falló después de {max_reintentos} intentos")
        return False, "Base de datos no disponible después de múltiples intentos"

    # --- Funciones de utilidad ---
    def formatear_guaranies(monto):
        """Formatea monto en guaraníes paraguayos"""
        return f"₲ {int(monto):,.0f}".replace(',', '.')

    def calcular_totales():
        """Calcula totales del carrito"""
        subtotal = sum(item['cantidad'] * item['precio'] for item in carrito_venta)
        descuento = 0
        total = subtotal - descuento
        return subtotal, descuento, total

    # --- FUNCIÓN PARA AGREGAR AL CARRITO ---
    def agregar_al_carrito(prod_id, prod_nombre, prod_precio, prod_stock, prod_unidad):
        """Agrega o actualiza producto en el carrito"""
        print(f"🛒 AGREGANDO AL CARRITO: {prod_nombre} (ID: {prod_id}) - Stock: {prod_stock}")
        
        # Buscar si ya existe en el carrito
        item_existente = None
        for i, item in enumerate(carrito_venta):
            if item['id'] == prod_id:
                item_existente = item
                break
        
        if item_existente:
            # Producto ya existe - aumentar cantidad
            if item_existente['cantidad'] < prod_stock:
                item_existente['cantidad'] += 1
                print(f"✅ Cantidad aumentada: {prod_nombre} x{item_existente['cantidad']}")
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ {prod_nombre} x{item_existente['cantidad']}", color="white"),
                    bgcolor=SUCCESS_COLOR,
                    duration=1500,
                )
            else:
                print(f"⚠️ Stock insuficiente para {prod_nombre}")
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"⚠️ Stock insuficiente para {prod_nombre}", color="white"),
                    bgcolor=WARNING_COLOR,
                    duration=2000,
                )
        else:
            # Producto nuevo - agregar al carrito
            nuevo_item = {
                'id': prod_id,
                'nombre': prod_nombre,
                'precio': prod_precio,
                'cantidad': 1,
                'stock': prod_stock,
                'unidad': prod_unidad
            }
            carrito_venta.append(nuevo_item)
            print(f"✅ Producto agregado: {prod_nombre} - ₲{prod_precio:,}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ {prod_nombre} agregado al carrito", color="white"),
                bgcolor=SUCCESS_COLOR,
                duration=1500,
            )
        
        # Mostrar notificación y actualizar carrito
        page.snack_bar.open = True
        page.update()
        
        if actualizar_carrito_fn:
            actualizar_carrito_fn()
        
        print(f"🛒 Carrito actual: {len(carrito_venta)} productos únicos")

    # --- FUNCIÓN PARA GENERAR Y MOSTRAR TICKET PDF ---
    def generar_y_mostrar_pdf(numero_venta, cliente_datos, carrito_items, totales_info):
        """Genera el PDF del ticket y lo abre automáticamente"""
        try:
            print(f"🎫 === GENERANDO TICKET PDF ===")
            print(f"📄 Número de venta: {numero_venta}")
            print(f"🛒 Items en carrito: {len(carrito_items)}")
            print(f"💰 Total: ₲{totales_info['total']:,}")
            
            # Generar PDF
            archivo_pdf = generar_ticket_pdf(
                numero_venta, 
                cliente_datos, 
                carrito_items, 
                totales_info, 
                current_user['nombre_completo']
            )
            
            if archivo_pdf:
                print(f"✅ PDF generado exitosamente: {archivo_pdf}")
                
                # Verificar que el archivo existe
                import os
                if os.path.exists(archivo_pdf):
                    file_size = os.path.getsize(archivo_pdf)
                    ruta_absoluta = os.path.abspath(archivo_pdf)
                    
                    print(f"📄 Archivo verificado: {file_size} bytes")
                    print(f"📂 Ubicación: {ruta_absoluta}")
                    
                    # Mostrar mensaje de éxito
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"📄 Ticket PDF generado: {archivo_pdf}", color="white"),
                        bgcolor=SUCCESS_COLOR,
                        duration=4000,
                    )
                    page.snack_bar.open = True
                    page.update()
                    
                    # Intentar abrir el PDF
                    if abrir_pdf(archivo_pdf):
                        print("📖 PDF abierto exitosamente")
                        return True
                    else:
                        print("⚠️ PDF creado pero no se pudo abrir automáticamente")
                        page.snack_bar = ft.SnackBar(
                            content=ft.Text(f"📄 PDF creado en: {ruta_absoluta}\n🖱️ Ábralo manualmente", color="white"),
                            bgcolor=WARNING_COLOR,
                            duration=6000,
                        )
                        page.snack_bar.open = True
                        page.update()
                        return True
                else:
                    raise Exception(f"El archivo PDF no se encontró: {archivo_pdf}")
            else:
                raise Exception("La función generar_ticket_pdf retornó None")
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error generando PDF: {error_msg}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ Error generando PDF: {error_msg}", color="white"),
                bgcolor=ERROR_COLOR,
                duration=5000,
            )
            page.snack_bar.open = True
            page.update()
            return False

    # --- FUNCIÓN PARA MOSTRAR TICKET EN PANTALLA (CORREGIDA) ---
    def mostrar_ticket_venta(numero_venta, cliente_datos, carrito_items, totales_info):
        """Muestra el ticket de venta como modal con opción de PDF - SIN DUPLICACIONES"""
        nonlocal modal_overlay
        
        now = datetime.now()
        fecha_hora = now.strftime("%d/%m/%Y %H:%M:%S")
        
        print(f"🧾 Mostrando ticket en pantalla: {numero_venta}")
        
        # Contenido del ticket
        ticket_content = ft.Column([
            # Encabezado
            ft.Container(
                content=ft.Column([
                    ft.Text("🌱 VIVERO ROCÍO", size=26, weight="bold", text_align=ft.TextAlign.CENTER, color=PRIMARY_COLOR),
                    ft.Text("Sistema de Gestión de Vivero", size=13, text_align=ft.TextAlign.CENTER),
                    ft.Text("TICKET DE VENTA", size=18, weight="bold", text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                padding=18,
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
            ),
            
            ft.Divider(height=3, color=PRIMARY_COLOR),
            
            # Info de la venta
            ft.Row([
                ft.Column([
                    ft.Text(f"🎫 Ticket: {numero_venta}", weight="bold", size=15, color=PRIMARY_COLOR),
                    ft.Text(f"📅 Fecha: {fecha_hora}", size=13),
                    ft.Text(f"👨‍💼 Cajero: {current_user['nombre_completo']}", size=13),
                ], expand=True, spacing=3),
                ft.Column([
                    ft.Text(f"👤 Cliente: {cliente_datos['nombre'] if cliente_datos else 'Cliente General'}", size=13, weight="bold"),
                    ft.Text(f"📞 Teléfono: {cliente_datos['telefono'] if cliente_datos and cliente_datos['telefono'] else 'N/A'}", size=12),
                    ft.Text(f"📧 Email: {cliente_datos['email'] if cliente_datos and cliente_datos['email'] else 'N/A'}", size=12),
                ], expand=True, spacing=3),
            ]),
            
            ft.Divider(),
            
            # Detalle de productos
            ft.Text("📋 DETALLE DE PRODUCTOS", weight="bold", size=16, text_align=ft.TextAlign.CENTER, color=PRIMARY_COLOR),
            ft.Container(height=8),
        ], spacing=12)
        
        # Agregar productos
        for i, item in enumerate(carrito_items, 1):
            producto_row = ft.Container(
                content=ft.Row([
                    ft.Text(f"{i}.", size=12, width=25),
                    ft.Text(item['nombre'], size=13, expand=2, weight="bold"),
                    ft.Text(f"x{item['cantidad']}", size=12, text_align=ft.TextAlign.CENTER, width=50),
                    ft.Text(f"₲{item['precio']:,.0f}".replace(',', '.'), size=12, text_align=ft.TextAlign.RIGHT, width=90),
                    ft.Text(f"₲{item['cantidad'] * item['precio']:,.0f}".replace(',', '.'), 
                           size=13, text_align=ft.TextAlign.RIGHT, weight="bold", width=100, color=PRIMARY_COLOR),
                ]),
                padding=ft.padding.symmetric(vertical=4, horizontal=8),
                border_radius=6,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREY) if i % 2 == 0 else None,
            )
            ticket_content.controls.append(producto_row)
        
        # Totales
        ticket_content.controls.extend([
            ft.Container(height=10),
            ft.Divider(color=PRIMARY_COLOR),
            
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("💰 SUBTOTAL:", weight="bold", size=16, expand=True),
                        ft.Text(f"₲{totales_info['subtotal']:,.0f}".replace(',', '.'), 
                               size=16, weight="bold", text_align=ft.TextAlign.RIGHT),
                    ]),
                    ft.Row([
                        ft.Text("🎯 TOTAL:", weight="bold", size=20, color=PRIMARY_COLOR, expand=True),
                        ft.Text(f"₲{totales_info['total']:,.0f}".replace(',', '.'), 
                               size=20, weight="bold", color=PRIMARY_COLOR, text_align=ft.TextAlign.RIGHT),
                    ]),
                ], spacing=8),
                padding=15,
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
            ),
            
            ft.Container(height=5),
            ft.Divider(),
            
            # Detalles de pago
            ft.Column([
                ft.Row([
                    ft.Text("💵 Pago recibido:", size=14, expand=True),
                    ft.Text(f"₲{totales_info['monto_pagado']:,.0f}".replace(',', '.'), 
                           size=14, text_align=ft.TextAlign.RIGHT),
                ]),
                ft.Row([
                    ft.Text("💸 Vuelto:", size=14, expand=True),
                    ft.Text(f"₲{totales_info['vuelto']:,.0f}".replace(',', '.'), 
                           size=14, text_align=ft.TextAlign.RIGHT, color=SUCCESS_COLOR if totales_info['vuelto'] >= 0 else ERROR_COLOR),
                ]),
                ft.Row([
                    ft.Text("💳 Método:", size=14, expand=True),
                    ft.Text(totales_info['metodo_pago'], size=14, text_align=ft.TextAlign.RIGHT, weight="bold"),
                ]),
            ], spacing=6),
            
            ft.Container(height=20),
            
            # Mensaje final
            ft.Container(
                content=ft.Column([
                    ft.Text("¡GRACIAS POR SU COMPRA!", size=18, text_align=ft.TextAlign.CENTER, 
                           weight="bold", color=PRIMARY_COLOR),
                    ft.Text("Vuelva pronto", size=14, text_align=ft.TextAlign.CENTER, 
                           style=ft.TextStyle(italic=True)),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=15,
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.05, SUCCESS_COLOR),
            ),
        ])
        
        def cerrar_ticket():
            """Cierra el modal del ticket"""
            nonlocal modal_overlay
            if modal_overlay in page.overlay:
                page.overlay.remove(modal_overlay)
            modal_overlay = None
            page.update()
            print("🔚 Ticket cerrado")
        
        def generar_pdf_handler():
            """Handler para generar PDF"""
            try:
                print(f"🖨️ Iniciando generación de PDF para {numero_venta}...")
                exito = generar_y_mostrar_pdf(numero_venta, cliente_datos, carrito_items, totales_info)
                if exito:
                    print(f"✅ PDF generado exitosamente para {numero_venta}")
                else:
                    print(f"❌ Error generando PDF para {numero_venta}")
            except Exception as e:
                print(f"❌ Error en handler PDF: {e}")
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Error generando PDF: {str(e)}", color="white"),
                    bgcolor=ERROR_COLOR,
                    duration=3000,
                )
                page.snack_bar.open = True
                page.update()
        
        # Modal del ticket - VERSIÓN ÚNICA Y CORREGIDA
        ticket_modal = ft.Container(
            content=ft.Column([
                # Header del modal
                ft.Row([
                    ft.Text("🧾 Ticket de Venta", size=22, weight="bold", expand=True, color=PRIMARY_COLOR),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        on_click=lambda e: cerrar_ticket(),
                        tooltip="Cerrar ticket",
                        icon_color=ERROR_COLOR,
                    ),
                ]),
                
                # Contenido del ticket con scroll CORREGIDO
                ft.Container(
                    content=ft.Column(
                        controls=[ticket_content], 
                        scroll=ft.ScrollMode.AUTO,
                        spacing=0
                    ),
                    height=520,
                    padding=18,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    border=ft.border.all(2, ft.Colors.GREY_300),
                ),
                
                # Botones de acción
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PICTURE_AS_PDF, size=20),
                            ft.Text("GENERAR PDF", size=15, weight="bold"),
                        ], spacing=6),
                        bgcolor=PRIMARY_COLOR,
                        color="white",
                        height=50,
                        on_click=lambda e: generar_pdf_handler(),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                    ),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE, size=20),
                            ft.Text("FINALIZAR", size=15, weight="bold"),
                        ], spacing=6),
                        bgcolor=SUCCESS_COLOR,
                        color="white",
                        height=50,
                        on_click=lambda e: cerrar_ticket(),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=18),
            width=580,
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=18,
            shadow=ft.BoxShadow(blur_radius=40, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
        )
        
        # Crear overlay
        modal_overlay = ft.Container(
            content=ft.Stack([
                ft.Container(
                    bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.BLACK), 
                    expand=True, 
                    on_click=lambda e: cerrar_ticket()
                ),
                ft.Container(
                    content=ticket_modal, 
                    alignment=ft.alignment.center, 
                    expand=True
                ),
            ]),
            expand=True,
        )
        
        page.overlay.append(modal_overlay)
        page.update()

    # --- OVERLAYS PARA GESTIÓN DE CAJA ---
    def mostrar_overlay_abrir_caja():
        """Modal para abrir caja"""
        nonlocal modal_overlay
        
        monto_field = ft.TextField(
            label="💰 Monto inicial (₲)",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=320,
            value="100000",
            autofocus=True,
            hint_text="Ingrese el monto con el que abre la caja",
            prefix_text="₲ ",
        )
        
        status_text = ft.Text("", size=12, text_align=ft.TextAlign.CENTER)
        
        def procesar_apertura():
            try:
                status_text.value = "⏳ Abriendo caja..."
                status_text.color = ft.Colors.BLUE
                page.update()
                
                monto_valor = monto_field.value or "0"
                monto_clean = str(monto_valor).replace('₲', '').replace('.', '').replace(',', '').replace(' ', '').strip()
                
                if not monto_clean or not monto_clean.isdigit():
                    status_text.value = "❌ Ingrese un monto válido"
                    status_text.color = ERROR_COLOR
                    page.update()
                    return
                
                monto = int(monto_clean)
                if monto < 0:
                    status_text.value = "❌ El monto no puede ser negativo"
                    status_text.color = ERROR_COLOR
                    page.update()
                    return
                
                sesion_id = abrir_caja(monto)
                
                if sesion_id:
                    sesion_actual["id"] = sesion_id
                    sesion_actual["monto_apertura"] = monto
                    
                    cerrar_overlay()
                    
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"✅ Caja abierta con {formatear_guaranies(monto)}", color="white"),
                        bgcolor=SUCCESS_COLOR,
                        duration=3000,
                    )
                    page.snack_bar.open = True
                    page.update()
                    
                    # Recargar interfaz
                    crud_view(content, page)
                else:
                    status_text.value = "❌ Error al abrir la caja"
                    status_text.color = ERROR_COLOR
                    page.update()
                    
            except Exception as ex:
                print(f"❌ Error en apertura: {ex}")
                status_text.value = f"❌ Error: {str(ex)}"
                status_text.color = ERROR_COLOR
                page.update()
        
        def cerrar_overlay():
            nonlocal modal_overlay
            if modal_overlay in page.overlay:
                page.overlay.remove(modal_overlay)
            modal_overlay = None
            page.update()
        
        modal_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LOCK_OPEN, size=32, color=SUCCESS_COLOR),
                    ft.Text("Abrir Caja", size=22, weight="bold", color=SUCCESS_COLOR),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                
                ft.Divider(color=SUCCESS_COLOR),
                
                ft.Text("Ingrese el monto inicial con el que abre la caja:", size=14, text_align=ft.TextAlign.CENTER),
                monto_field,
                status_text,
                
                ft.Container(height=15),
                
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda e: cerrar_overlay()),
                    ft.ElevatedButton(
                        "✅ ABRIR CAJA",
                        bgcolor=SUCCESS_COLOR,
                        color="white",
                        on_click=lambda e: procesar_apertura(),
                        width=150,
                        height=45,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=18),
            width=380,
            padding=25,
            border_radius=18,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=25, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
        )
        
        modal_overlay = ft.Container(
            content=ft.Stack([
                ft.Container(bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK), expand=True, on_click=lambda e: cerrar_overlay()),
                ft.Container(content=modal_content, alignment=ft.alignment.center, expand=True),
            ]),
            expand=True,
        )
        
        page.overlay.append(modal_overlay)
        page.update()

    def mostrar_overlay_cerrar_caja():
        """Modal para cerrar caja"""
        nonlocal modal_overlay
        
        # Calcular ventas del día
        ventas_dia = obtener_ventas_del_dia()
        total_ventas_dia = sum(venta[1] for venta in ventas_dia)
        monto_esperado = sesion_actual["monto_apertura"] + total_ventas_dia
        
        monto_field = ft.TextField(
            label="💰 Monto de cierre (₲)", 
            keyboard_type=ft.KeyboardType.NUMBER, 
            width=320, 
            value=str(int(monto_esperado)),
            hint_text="Cuente el dinero físico en caja",
            prefix_text="₲ ",
        )
        
        obs_field = ft.TextField(
            label="📝 Observaciones (opcional)", 
            multiline=True, 
            max_lines=3, 
            width=320,
            hint_text="Comentarios sobre el cierre de caja",
        )
        
        status_text = ft.Text("", size=12, text_align=ft.TextAlign.CENTER)
        
        def procesar_cierre():
            try:
                status_text.value = "⏳ Cerrando caja..."
                status_text.color = ft.Colors.BLUE
                page.update()
                
                monto_str = monto_field.value.replace('₲', '').replace('.', '').replace(',', '').strip()
                monto = int(monto_str) if monto_str else 0
                obs = obs_field.value or ""
                
                if cerrar_caja(sesion_actual["id"], monto, obs):
                    # Calcular diferencia para mostrar
                    diferencia = monto - monto_esperado
                    
                    # Limpiar variables
                    sesion_actual["id"] = None
                    sesion_actual["monto_apertura"] = 0
                    carrito_venta.clear()
                    
                    cerrar_overlay()
                    
                    # Mensaje de cierre con detalles
                    mensaje_cierre = f"✅ Caja cerrada\n💰 Esperado: {formatear_guaranies(monto_esperado)}\n💵 Contado: {formatear_guaranies(monto)}"
                    if diferencia != 0:
                        signo = "+" if diferencia > 0 else ""
                        mensaje_cierre += f"\n📊 Diferencia: {signo}{formatear_guaranies(diferencia)}"
                    
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(mensaje_cierre, color="white"),
                        bgcolor=SUCCESS_COLOR,
                        duration=5000,
                    )
                    page.snack_bar.open = True
                    page.update()
                    
                    # Recargar interfaz
                    crud_view(content, page)
                else:
                    status_text.value = "❌ Error cerrando la caja"
                    status_text.color = ERROR_COLOR
                    page.update()
            except ValueError:
                status_text.value = "❌ Ingrese un monto válido"
                status_text.color = ERROR_COLOR
                page.update()
        
        def cerrar_overlay():
            nonlocal modal_overlay
            if modal_overlay in page.overlay:
                page.overlay.remove(modal_overlay)
            modal_overlay = None
            page.update()
        
        modal_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LOCK, size=32, color=WARNING_COLOR),
                    ft.Text("Cerrar Caja", size=22, weight="bold", color=WARNING_COLOR),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                
                ft.Divider(color=WARNING_COLOR),
                
                # Resumen
                ft.Container(
                    content=ft.Column([
                        ft.Text("📊 RESUMEN DEL DÍA", size=14, weight="bold", text_align=ft.TextAlign.CENTER),
                        ft.Text(f"💰 Apertura: {formatear_guaranies(sesion_actual['monto_apertura'])}", size=12),
                        ft.Text(f"🛒 Ventas: {formatear_guaranies(total_ventas_dia)}", size=12),
                        ft.Text(f"🎯 Esperado: {formatear_guaranies(monto_esperado)}", size=13, weight="bold", color=PRIMARY_COLOR),
                    ], spacing=4),
                    padding=12,
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.1, WARNING_COLOR),
                ),
                
                ft.Text("Cuente el dinero físico en caja:", size=14),
                monto_field,
                obs_field,
                status_text,
                
                ft.Container(height=10),
                
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda e: cerrar_overlay()),
                    ft.ElevatedButton(
                        "🔒 CERRAR CAJA",
                        bgcolor=WARNING_COLOR,
                        color="white",
                        on_click=lambda e: procesar_cierre(),
                        width=150,
                        height=45,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=15),
            width=380,
            padding=25,
            border_radius=18,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=25, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
        )
        
        modal_overlay = ft.Container(
            content=ft.Stack([
                ft.Container(bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK), expand=True, on_click=lambda e: cerrar_overlay()),
                ft.Container(content=modal_content, alignment=ft.alignment.center, expand=True),
            ]),
            expand=True,
        )
        
        page.overlay.append(modal_overlay)
        page.update()

    def mostrar_overlay_pago():
        """Modal para procesar pago con datos completos del cliente"""
        nonlocal modal_overlay
        
        clientes = obtener_clientes()
        subtotal, descuento, total = calcular_totales()
        
        print(f"💳 Iniciando proceso de pago - Total: {formatear_guaranies(total)}")
        
        cliente_dropdown = ft.Dropdown(
            label="👤 Cliente (opcional)",
            options=[ft.dropdown.Option(key=str(c[0]), text=f"{c[1]}") for c in clientes],
            width=420,
            hint_text="Seleccione un cliente o deje vacío",
        )
        
        # Contenedor para datos del cliente
        cliente_info = ft.Container(
            content=ft.Text("💡 Seleccione un cliente para ver sus datos", size=12, color=ft.Colors.GREY_600),
            padding=12,
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREY),
            visible=False,
        )
        
        monto_field = ft.TextField(
            label="💵 Monto recibido (₲)",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=420,
            autofocus=True,
            hint_text=f"Mínimo: {formatear_guaranies(total)}",
            prefix_text="₲ ",
        )
        
        metodo_dropdown = ft.Dropdown(
            label="💳 Método de pago",
            options=[
                ft.dropdown.Option("Efectivo"),
                ft.dropdown.Option("Tarjeta Débito"),
                ft.dropdown.Option("Tarjeta Crédito"),
                ft.dropdown.Option("Transferencia"),
                ft.dropdown.Option("Cheque"),
            ],
            value="Efectivo",
            width=420,
        )
        
        vuelto_text = ft.Text("💸 Vuelto: ₲ 0", size=18, weight="bold", color=SUCCESS_COLOR)
        status_text = ft.Text("", size=12, text_align=ft.TextAlign.CENTER)
        
        def actualizar_cliente_info(e):
            """Actualiza la información del cliente seleccionado"""
            if cliente_dropdown.value:
                cliente_data = obtener_cliente_por_id(int(cliente_dropdown.value))
                if cliente_data:
                    cliente_info.content = ft.Column([
                        ft.Text(f"📞 Teléfono: {cliente_data[2] or 'No disponible'}", size=12),
                        ft.Text(f"📧 Email: {cliente_data[3] or 'No disponible'}", size=12),
                        ft.Text(f"📍 Dirección: {cliente_data[4] or 'No disponible'}", size=12),
                    ], spacing=3)
                    cliente_info.visible = True
                    print(f"👤 Cliente seleccionado: {cliente_data[1]}")
                else:
                    cliente_info.visible = False
            else:
                cliente_info.visible = False
            page.update()
        
        cliente_dropdown.on_change = actualizar_cliente_info
        
        def calcular_vuelto():
            """Calcula y muestra el vuelto en tiempo real"""
            try:
                monto_str = monto_field.value.replace('₲', '').replace('.', '').replace(',', '').strip()
                monto = int(monto_str) if monto_str else 0
                vuelto = monto - total
                
                if vuelto >= 0:
                    vuelto_text.value = f"💸 Vuelto: {formatear_guaranies(vuelto)}"
                    vuelto_text.color = SUCCESS_COLOR
                else:
                    vuelto_text.value = f"⚠️ Falta: {formatear_guaranies(abs(vuelto))}"
                    vuelto_text.color = ERROR_COLOR
                page.update()
            except ValueError:
                vuelto_text.value = "💸 Vuelto: ₲ 0"
                vuelto_text.color = SUCCESS_COLOR
                page.update()
        
        def procesar_pago():
            """Procesa el pago completo"""
            try:
                status_text.value = "⏳ Procesando pago..."
                status_text.color = ft.Colors.BLUE
                page.update()
                
                monto_str = monto_field.value.replace('₲', '').replace('.', '').replace(',', '').strip()
                monto_pagado = int(monto_str) if monto_str else 0
                
                if monto_pagado < total:
                    status_text.value = f"❌ Monto insuficiente. Faltan {formatear_guaranies(total - monto_pagado)}"
                    status_text.color = ERROR_COLOR
                    page.update()
                    return
                
                vuelto = monto_pagado - total
                cliente_id = int(cliente_dropdown.value) if cliente_dropdown.value else None
                metodo = metodo_dropdown.value
                
                print(f"💳 Procesando: Total={formatear_guaranies(total)}, Pagado={formatear_guaranies(monto_pagado)}, Vuelto={formatear_guaranies(vuelto)}")
                
                # Obtener datos del cliente para el ticket
                cliente_datos = None
                if cliente_id:
                    cliente_datos = obtener_cliente_por_id(cliente_id)
                    if cliente_datos:
                        cliente_datos = {
                            'nombre': cliente_datos[1],
                            'telefono': cliente_datos[2],
                            'email': cliente_datos[3],
                            'direccion': cliente_datos[4]
                        }
                        print(f"👤 Datos del cliente para ticket: {cliente_datos['nombre']}")
                
                # Guardar venta
                exito, resultado = guardar_venta(cliente_id, subtotal, descuento, total, monto_pagado, vuelto, metodo, carrito_venta)
                
                if exito:
                    print(f"🎉 Venta procesada exitosamente: {resultado}")
                    
                    # Guardar datos para el ticket
                    carrito_backup = carrito_venta.copy()
                    totales_info = {
                        'subtotal': subtotal,
                        'descuento': descuento,
                        'total': total,
                        'monto_pagado': monto_pagado,
                        'vuelto': vuelto,
                        'metodo_pago': metodo
                    }
                    
                    # Limpiar carrito
                    carrito_venta.clear()
                    cerrar_overlay()
                    
                    # Actualizar vistas
                    if actualizar_carrito_fn:
                        actualizar_carrito_fn()
                    if actualizar_ventas_fn:
                        actualizar_ventas_fn()
                    
                    # Mostrar ticket
                    mostrar_ticket_venta(resultado, cliente_datos, carrito_backup, totales_info)
                    
                else:
                    status_text.value = f"❌ Error: {resultado}"
                    status_text.color = ERROR_COLOR
                    page.update()
                    
            except Exception as ex:
                print(f"❌ Error procesando pago: {ex}")
                status_text.value = f"❌ Error: {str(ex)}"
                status_text.color = ERROR_COLOR
                page.update()
        
        def cerrar_overlay():
            nonlocal modal_overlay
            if modal_overlay in page.overlay:
                page.overlay.remove(modal_overlay)
            modal_overlay = None
            page.update()
        
        monto_field.on_change = lambda e: calcular_vuelto()
        
        modal_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PAYMENT, size=32, color=PRIMARY_COLOR),
                    ft.Text("Procesar Pago", size=24, weight="bold", color=PRIMARY_COLOR),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                
                ft.Divider(color=PRIMARY_COLOR),
                
                # Total destacado
                ft.Container(
                    content=ft.Column([
                        ft.Text("💰 TOTAL A COBRAR", size=16, text_align=ft.TextAlign.CENTER, color=ft.Colors.GREY_700),
                        ft.Text(f"{formatear_guaranies(total)}", size=24, weight="bold", color=PRIMARY_COLOR, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    padding=18,
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
                    alignment=ft.alignment.center,
                ),
                
                # Campos del formulario
                cliente_dropdown,
                cliente_info,
                monto_field,
                metodo_dropdown,
                
                # Vuelto
                ft.Container(
                    content=vuelto_text,
                    padding=12,
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.1, SUCCESS_COLOR),
                    alignment=ft.alignment.center,
                ),
                
                status_text,
                
                ft.Container(height=10),
                
                # Botones
                ft.Row([
                    ft.TextButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CANCEL, size=16),
                            ft.Text("Cancelar", size=14),
                        ], spacing=4),
                        on_click=lambda e: cerrar_overlay(),
                    ),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PAYMENT, size=18),
                            ft.Text("CONFIRMAR PAGO", size=16, weight="bold"),
                        ], spacing=6),
                        bgcolor=SUCCESS_COLOR,
                        color="white",
                        on_click=lambda e: procesar_pago(),
                        height=50,
                        width=200,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
            ], spacing=18, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=480,
            padding=30,
            border_radius=20,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=30, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
        )
        
        modal_overlay = ft.Container(
            content=ft.Stack([
                ft.Container(bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK), expand=True, on_click=lambda e: cerrar_overlay()),
                ft.Container(content=modal_content, alignment=ft.alignment.center, expand=True),
            ]),
            expand=True,
        )
        
        page.overlay.append(modal_overlay)
        page.update()
        monto_field.focus()

    # --- COMPONENTES UI DE 3 COLUMNAS ---
    def crear_header():
        """Header mejorado con botón de regreso"""
        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=PRIMARY_COLOR,
                    icon_size=28,
                    tooltip="Volver al Dashboard",
                    on_click=lambda e: volver_dashboard(),
                    bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
                    style=ft.ButtonStyle(shape=ft.CircleBorder()),
                ),
                ft.Row([
                    ft.Icon(ft.Icons.POINT_OF_SALE, size=28, color=PRIMARY_COLOR),
                    ft.Text("Sistema de Ventas - PdV", size=24, weight="bold", color=PRIMARY_COLOR),
                ], spacing=8),
                ft.Container(expand=True),
                ft.Column([
                    ft.Text(f"Operador: {current_user['nombre_completo']}", size=14, weight="bold"),
                    ft.Text(datetime.now().strftime("%d/%m/%Y %H:%M"), size=12, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
            ], alignment=ft.MainAxisAlignment.START, spacing=12),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )

    def crear_estado_caja():
        """Estado de caja con información detallada"""
        sesion_info = obtener_sesion_activa()
        
        if sesion_info:
            sesion_actual["id"] = sesion_info[0]
            sesion_actual["monto_apertura"] = sesion_info[1]
            
            return ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.CIRCLE, size=16, color=SUCCESS_COLOR),
                        ft.Text("Caja Abierta", size=16, weight="bold", color=SUCCESS_COLOR),
                        ft.Text(f"- Apertura: {formatear_guaranies(sesion_info[1])}", size=14),
                        ft.Text(f"- {sesion_info[3]}", size=12, color=ft.Colors.GREY_600),
                    ], spacing=8),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Cerrar Caja",
                        icon=ft.Icons.LOCK,
                        bgcolor=WARNING_COLOR,
                        color="white",
                        height=40,
                        on_click=lambda e: mostrar_overlay_cerrar_caja(),
                    ),
                ], alignment=ft.MainAxisAlignment.START, spacing=12),
                padding=15,
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.1, SUCCESS_COLOR),
                border=ft.border.all(2, SUCCESS_COLOR),
            )
        else:
            return ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.CIRCLE, size=16, color=ERROR_COLOR),
                        ft.Text("Caja Cerrada", size=16, weight="bold", color=ERROR_COLOR),
                        ft.Text("- Debe abrir caja para realizar ventas", size=14),
                    ], spacing=8),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Abrir Caja",
                        icon=ft.Icons.LOCK_OPEN,
                        bgcolor=SUCCESS_COLOR,
                        color="white",
                        height=40,
                        on_click=lambda e: mostrar_overlay_abrir_caja(),
                    ),
                ], alignment=ft.MainAxisAlignment.START, spacing=12),
                padding=15,
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.1, ERROR_COLOR),
                border=ft.border.all(2, ERROR_COLOR),
            )

    def crear_columna_productos():
        """Columna izquierda - Catálogo de productos"""
        productos = obtener_productos()
        
        search_field = ft.TextField(
            label="🔍 Buscar producto",
            prefix_icon=ft.Icons.SEARCH,
            height=45,
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
        )
        productos_list = ft.Column([], spacing=8, scroll=ft.ScrollMode.AUTO)
        
        def filtrar_productos(texto):
            productos_list.controls.clear()
            productos_filtrados = [p for p in productos if texto.lower() in p[1].lower()] if texto else productos
            
            if not productos_filtrados:
                productos_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.SEARCH_OFF, size=60, color=ft.Colors.GREY_400),
                            ft.Text("No hay productos disponibles", color=ft.Colors.GREY_600, size=14),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        alignment=ft.alignment.center,
                        height=150,
                    )
                )
            else:
                for producto in productos_filtrados:
                    id_prod, nombre, categoria, precio, stock, unidad = producto
                    
                    def crear_handler(prod_id, prod_nombre, prod_precio, prod_stock, prod_unidad):
                        def handler(e):
                            agregar_al_carrito(prod_id, prod_nombre, prod_precio, prod_stock, prod_unidad)
                        return handler
                    
                    stock_color = SUCCESS_COLOR if stock > 10 else WARNING_COLOR if stock > 0 else ERROR_COLOR
                    
                    producto_card = ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(nombre, weight="bold", size=15, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(f"📂 {categoria}", size=12, color=ft.Colors.GREY_600),
                                ft.Row([
                                    ft.Text(f"💰 {formatear_guaranies(precio)}", size=13, weight="bold", color=PRIMARY_COLOR),
                                    ft.Text(f"📦 Stock: {stock}", size=12, color=stock_color, weight="bold"),
                                ], spacing=10),
                            ], expand=True, spacing=3),
                            ft.IconButton(
                                icon=ft.Icons.ADD_SHOPPING_CART,
                                icon_color="white",
                                bgcolor=PRIMARY_COLOR,
                                on_click=crear_handler(id_prod, nombre, precio, stock, unidad),
                                icon_size=20,
                                width=45,
                                height=45,
                                tooltip=f"Agregar {nombre}",
                            ),
                        ], spacing=10),
                        padding=12,
                        border_radius=10,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        ink=True,
                        shadow=ft.BoxShadow(blur_radius=3, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                    )
                    productos_list.controls.append(producto_card)
            
            page.update()
        
        search_field.on_change = lambda e: filtrar_productos(e.control.value)
        filtrar_productos("")
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INVENTORY, color=PRIMARY_COLOR, size=24),
                    ft.Text("Catálogo de Productos", size=18, weight="bold", color=PRIMARY_COLOR),
                ], spacing=8),
                search_field,
                ft.Container(
                    content=productos_list,
                    height=480,
                ),
            ], spacing=12),
            padding=15,
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.GREY),
            expand=True,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )

    def crear_columna_carrito():
        """Columna central - Carrito de Venta"""
        nonlocal actualizar_carrito_fn
        
        carrito_list = ft.Column([], spacing=10, scroll=ft.ScrollMode.AUTO)
        
        totales_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Subtotal:", weight="bold", size=16),
                    ft.Text("₲ 0", weight="bold", text_align=ft.TextAlign.RIGHT, expand=True, size=16),
                ]),
                ft.Divider(height=2, color=PRIMARY_COLOR),
                ft.Row([
                    ft.Text("TOTAL:", size=20, weight="bold", color=PRIMARY_COLOR),
                    ft.Text("₲ 0", size=20, weight="bold", color=PRIMARY_COLOR, text_align=ft.TextAlign.RIGHT, expand=True),
                ]),
            ], spacing=8),
            padding=15,
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
            border=ft.border.all(2, PRIMARY_COLOR),
        )
        
        pagar_button = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.PAYMENT, color="white", size=24),
                ft.Text("PROCESAR PAGO", size=16, weight="bold", color="white"),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            bgcolor=SUCCESS_COLOR,
            color="white",
            height=55,
            on_click=lambda e: mostrar_overlay_pago() if carrito_venta and sesion_actual["id"] else None,
            disabled=True,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                shadow_color=SUCCESS_COLOR,
                elevation=8,
            ),
        )
        
        def actualizar_carrito():
            carrito_list.controls.clear()
            
            if not carrito_venta:
                carrito_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.SHOPPING_CART_OUTLINED, size=80, color=ft.Colors.GREY_400),
                            ft.Text("Carrito vacío", color=ft.Colors.GREY_600, size=18, weight="bold"),
                            ft.Text("Agregue productos del catálogo", color=ft.Colors.GREY_500, size=14),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                        alignment=ft.alignment.center,
                        height=200,
                    )
                )
            else:
                for i, item in enumerate(carrito_venta):
                    cantidad_field = ft.TextField(
                        value=str(item['cantidad']),
                        width=80,
                        height=40,
                        text_align=ft.TextAlign.CENTER,
                        keyboard_type=ft.KeyboardType.NUMBER,
                        border_radius=8,
                        bgcolor=ft.Colors.WHITE,
                        text_size=14,
                    )
                    
                    def crear_handler_cantidad(idx):
                        def handler(e):
                            try:
                                nueva_cantidad = int(e.control.value)
                                if nueva_cantidad > 0 and nueva_cantidad <= carrito_venta[idx]['stock']:
                                    carrito_venta[idx]['cantidad'] = nueva_cantidad
                                    actualizar_carrito()
                                elif nueva_cantidad <= 0:
                                    carrito_venta.pop(idx)
                                    actualizar_carrito()
                            except ValueError:
                                actualizar_carrito()
                        return handler
                    
                    cantidad_field.on_change = crear_handler_cantidad(i)
                    
                    def crear_handler_eliminar(idx):
                        def handler(e):
                            if idx < len(carrito_venta):
                                carrito_venta.pop(idx)
                                actualizar_carrito()
                        return handler
                    
                    item_card = ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(item['nombre'], weight="bold", size=15, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(f"Precio: {formatear_guaranies(item['precio'])}", size=13, color=ft.Colors.GREY_600),
                                ], expand=True, spacing=3),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ERROR_COLOR,
                                    on_click=crear_handler_eliminar(i),
                                    icon_size=20,
                                    tooltip="Eliminar producto",
                                ),
                            ]),
                            ft.Row([
                                ft.Text("Cantidad:", size=14, weight="bold"),
                                cantidad_field,
                                ft.Text("Total:", size=14, weight="bold", expand=True, text_align=ft.TextAlign.RIGHT),
                                ft.Text(formatear_guaranies(item['cantidad'] * item['precio']), 
                                       weight="bold", size=15, color=PRIMARY_COLOR),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ], spacing=8),
                        padding=15,
                        border_radius=10,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        shadow=ft.BoxShadow(blur_radius=3, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                    )
                    carrito_list.controls.append(item_card)
            
            # Actualizar totales
            subtotal, descuento, total = calcular_totales()
            totales_container.content.controls[0].controls[1].value = formatear_guaranies(subtotal)
            totales_container.content.controls[2].controls[1].value = formatear_guaranies(total)
            
            # Actualizar botón
            pagar_button.disabled = not (carrito_venta and sesion_actual["id"])
            pagar_button.bgcolor = SUCCESS_COLOR if not pagar_button.disabled else ft.Colors.GREY_400
            
            page.update()
        
        actualizar_carrito_fn = actualizar_carrito
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SHOPPING_CART, color=PRIMARY_COLOR, size=24),
                    ft.Text("Carrito de Venta", size=18, weight="bold", color=PRIMARY_COLOR),
                ], spacing=8),
                ft.Container(
                    content=carrito_list,
                    height=300,
                ),
                totales_container,
                pagar_button,
            ], spacing=15),
            padding=15,
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.GREY),
            width=400,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )

    def crear_columna_ventas():
        """Columna derecha - Ventas del día"""
        nonlocal actualizar_ventas_fn
        
        ventas_list = ft.Column([], spacing=8, scroll=ft.ScrollMode.AUTO)
        total_ventas_text = ft.Text("Total del día: ₲ 0", size=16, weight="bold", color=PRIMARY_COLOR)
        
        def actualizar_ventas():
            ventas_list.controls.clear()
            ventas = obtener_ventas_del_dia()
            
            if not ventas:
                ventas_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.RECEIPT_LONG, size=60, color=ft.Colors.GREY_400),
                            ft.Text("Sin ventas", color=ft.Colors.GREY_600, size=16, weight="bold"),
                            ft.Text("Las ventas aparecerán aquí", color=ft.Colors.GREY_500, size=12),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                        alignment=ft.alignment.center,
                        height=150,
                    )
                )
                total_ventas_text.value = "Total del día: ₲ 0"
            else:
                total_dia = sum(venta[1] for venta in ventas)
                total_ventas_text.value = f"Total del día: {formatear_guaranies(total_dia)}"
                
                for venta in ventas:
                    numero, total, metodo, fecha, cliente, vendedor = venta
                    fecha_corta = fecha.split(' ')[1][:5] if fecha else "N/A"
                    
                    venta_card = ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(f"#{numero}", weight="bold", size=12, color=PRIMARY_COLOR),
                                    ft.Text(f"🕐 {fecha_corta}", size=10, color=ft.Colors.GREY_600),
                                ], spacing=2),
                                ft.Column([
                                    ft.Text(formatear_guaranies(total), weight="bold", size=13, text_align=ft.TextAlign.RIGHT),
                                    ft.Text(metodo, size=10, color=ft.Colors.GREY_600, text_align=ft.TextAlign.RIGHT),
                                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                            ]),
                            ft.Row([
                                ft.Text(f"👤 {cliente or 'Cliente General'}", size=10, color=ft.Colors.GREY_500, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(f"👨‍💼 {vendedor or 'N/A'}", size=10, color=ft.Colors.GREY_500, text_align=ft.TextAlign.RIGHT),
                            ]),
                        ], spacing=5),
                        padding=10,
                        border_radius=8,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        shadow=ft.BoxShadow(blur_radius=2, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                    )
                    ventas_list.controls.append(venta_card)
            
            page.update()
        
        actualizar_ventas_fn = actualizar_ventas
        actualizar_ventas()
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.RECEIPT_LONG, color=PRIMARY_COLOR, size=24),
                    ft.Text("Ventas del Día", size=18, weight="bold", color=PRIMARY_COLOR),
                ], spacing=8),
                total_ventas_text,
                ft.Container(
                    content=ventas_list,
                    height=450,
                ),
            ], spacing=12),
            padding=15,
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.GREY),
            width=350,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )

    # --- LAYOUT PRINCIPAL DE 3 COLUMNAS ---
    header = crear_header()
    estado_caja = crear_estado_caja()
    
    # Contenido según estado de caja
    if sesion_actual["id"]:
        columna_productos = crear_columna_productos()
        columna_carrito = crear_columna_carrito()
        columna_ventas = crear_columna_ventas()
        
        # Inicializar función de actualización del carrito
        if actualizar_carrito_fn:
            actualizar_carrito_fn()
        
        # Layout de 3 columnas SIN scroll horizontal
        contenido_principal = ft.Row([
            columna_productos,      # Izquierda - Productos
            columna_carrito,        # Centro - Carrito
            columna_ventas,         # Derecha - Ventas del día
        ], spacing=15)
    else:
        contenido_principal = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_OUTLINE, size=100, color=ft.Colors.GREY_400),
                ft.Text("Caja Cerrada", size=24, weight="bold", color=ft.Colors.GREY_600),
                ft.Text("Debe abrir caja para realizar ventas", size=16, color=ft.Colors.GREY_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            alignment=ft.alignment.center,
            expand=True,
        )

    # Layout principal con scroll vertical solamente
    layout_principal = ft.Column([
        header,
        estado_caja,
        contenido_principal,
    ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

    # Agregar al contenido de la página
    if hasattr(content, 'controls'):
        content.controls.append(layout_principal)
    else:
        content.content = layout_principal
    
    page.update()
    print("✅ Módulo de ventas PdV 3 COLUMNAS COMPLETO cargado")