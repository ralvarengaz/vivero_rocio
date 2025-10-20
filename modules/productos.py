import flet as ft
import sqlite3
from modules import dashboard
from modules.plantas import TODAS_PLANTAS

DB = "data/vivero.db"
PRIMARY_COLOR = "#2E7D32"
ACCENT_COLOR = "#66BB6A"

def crud_view(content, page=None):
    content.controls.clear()

    # --- Función para mostrar avisos ---
    def show_snackbar(msg: str, color: str):
        snackbar = ft.SnackBar(
            content=ft.Text(msg, color="white"),
            bgcolor=color,
            duration=3000,
        )
        page.open(snackbar)

    # --- Función para verificar estructura de la tabla ---
    def verificar_estructura_tabla():
        """Verifica qué columnas tiene la tabla productos"""
        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(productos)")
            columnas = cur.fetchall()
            conn.close()
            print("📋 Columnas de la tabla productos:")
            for col in columnas:
                print(f"  - {col[1]} ({col[2]})")
            return [col[1] for col in columnas]  # Retorna solo los nombres
        except Exception as e:
            print(f"❌ Error verificando estructura: {e}")
            return []

    # Verificar estructura al inicio
    columnas_disponibles = verificar_estructura_tabla()

    # --- Campo Nombre con sugerencias ---
    nombre = ft.TextField(label="Nombre", width=300, hint_text="Ej: Rosa", prefix_icon=ft.icons.SPA)
    sugerencias = ft.Column(spacing=2, visible=False)

    def actualizar_sugerencias(e):
        texto = nombre.value.lower()
        sugerencias.controls.clear()
        if texto:
            coincidencias = [p for p in TODAS_PLANTAS if texto in p.lower()]
            for planta in coincidencias[:5]:
                sugerencias.controls.append(
                    ft.TextButton(
                        text=planta,
                        on_click=lambda ev, v=planta: seleccionar_sugerencia(v),
                        style=ft.ButtonStyle(color=PRIMARY_COLOR),
                    )
                )
            sugerencias.visible = bool(coincidencias)
        else:
            sugerencias.visible = False
        page.update()

    def seleccionar_sugerencia(valor):
        nombre.value = valor
        sugerencias.visible = False
        page.update()

    nombre.on_change = actualizar_sugerencias

    # --- Categoría ---
    categoria = ft.Dropdown(
        label="Categoría",
        width=300,
        options=[
            ft.dropdown.Option("Ornamentales"),
            ft.dropdown.Option("Cítricos"),
            ft.dropdown.Option("Frutales"),
            ft.dropdown.Option("Forestales"),
            ft.dropdown.Option("Medicinales"),
            ft.dropdown.Option("Jardín e insumos"),
        ],
    )

    # --- Unidad ---
    unidad = ft.Dropdown(
        label="Unidad",
        width=150,
        options=[
            ft.dropdown.Option("Unitario"),
            ft.dropdown.Option("m²"),
        ],
    )

    precio_compra = ft.TextField(label="Precio Compra (Gs.)", width=200, hint_text="Ej: 12000", prefix_icon=ft.icons.MONEY)
    precio_venta = ft.TextField(label="Precio Venta (Gs.)", width=200, hint_text="Ej: 15000", prefix_icon=ft.icons.PAID)
    
    # Campo de stock
    stock = ft.TextField(label="Stock", width=150, hint_text="Ej: 100", prefix_icon=ft.icons.INVENTORY, value="0")

    # --- Tabla y búsqueda (CORREGIDA) ---
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", text_align="center", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Nombre", text_align="left", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Categoría", text_align="center", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Unidad", text_align="center", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("P. Compra", text_align="center", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("P. Venta", text_align="center", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Stock", text_align="center", color=PRIMARY_COLOR)),
        ],
        rows=[],
        column_spacing=8,
    )

    busqueda = ft.TextField(
        label="Buscar producto",
        width=300,
        prefix_icon=ft.icons.SEARCH,
        on_change=lambda e: refrescar_tabla(busqueda.value),
    )

    # --- Variables de estado ---
    selected_id = {"id": None}
    producto_original = {"data": None}
    error_msg = ft.Text("", color="red")

    # --- Funciones auxiliares ---
    def crear_indice_unico():
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_productos_nombre_nocase
            ON productos (nombre COLLATE NOCASE)
        """)
        conn.commit()
        conn.close()

    def existe_producto(nombre_val: str, excluir_id: int | None = None) -> bool:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        if excluir_id is None:
            cur.execute("SELECT 1 FROM productos WHERE nombre = ? COLLATE NOCASE LIMIT 1", (nombre_val.strip(),))
        else:
            cur.execute(
                "SELECT 1 FROM productos WHERE nombre = ? COLLATE NOCASE AND id <> ? LIMIT 1",
                (nombre_val.strip(), excluir_id),
            )
        found = cur.fetchone() is not None
        conn.close()
        return found

    crear_indice_unico()

    def limpiar_form():
        nombre.value = ""
        categoria.value = None
        unidad.value = None
        precio_compra.value = ""
        precio_venta.value = ""
        stock.value = "0"
        selected_id["id"] = None
        producto_original["data"] = None
        sugerencias.visible = False
        error_msg.value = ""
        page.update()

    def agregar_producto(e):
        # Validar nombre
        if not nombre.value or not nombre.value.strip():
            error_msg.value = "⚠️ El nombre es obligatorio"
            page.update()
            return
        
        # Limpiar el nombre
        nombre_limpio = nombre.value.strip()
        
        # Validar duplicado
        if existe_producto(nombre_limpio):
            error_msg.value = "⚠️ Ya existe un producto con este nombre"
            page.update()
            return
        
        # Validar otros campos
        if not categoria.value or not unidad.value or not precio_compra.value or not precio_venta.value:
            error_msg.value = "⚠️ Todos los campos son obligatorios"
            page.update()
            return
        
        # Validar números
        try:
            pc = float(precio_compra.value.replace(".", "").replace(",", ""))
            pv = float(precio_venta.value.replace(".", "").replace(",", ""))
            st = int(stock.value or "0")
        except:
            error_msg.value = "⚠️ Los precios y stock deben ser números válidos"
            page.update()
            return

        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            
            # ✅ INSERCIÓN CORREGIDA - Incluir TODOS los campos obligatorios
            cur.execute("""
                INSERT INTO productos (
                    nombre, 
                    categoria, 
                    unidad, 
                    precio_compra, 
                    precio_venta, 
                    unidad_medida, 
                    stock,
                    fecha_creacion,
                    fecha_actualizacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
            """, (
                nombre_limpio,           # nombre
                categoria.value,         # categoria  
                unidad.value,           # unidad (NOT NULL)
                pc,                     # precio_compra
                pv,                     # precio_venta
                unidad.value,           # unidad_medida (usar mismo valor que unidad)
                st                      # stock
            ))
            
            conn.commit()
            conn.close()
            
            limpiar_form()
            refrescar_tabla()
            show_snackbar("✅ Producto agregado correctamente", "#2E7D32")
            
        except sqlite3.IntegrityError as e:
            error_msg.value = f"⚠️ Error de integridad: {str(e)}"
            page.update()
            return
        except Exception as ex:
            error_msg.value = f"⚠️ Error: {str(ex)}"
            page.update()
            return
    def refrescar_tabla(filtro: str = ""):
        """Función COMPLETAMENTE CORREGIDA para manejar cualquier estructura de tabla"""
        tabla.rows.clear()
        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            
            # Consulta adaptable con nombres específicos de columnas
            if filtro:
                cur.execute("""
                    SELECT 
                        id,
                        nombre,
                        categoria,
                        COALESCE(unidad_medida, unidad, 'Unitario') as unidad_final,
                        COALESCE(precio_compra, precio, 0) as precio_compra_final,
                        COALESCE(precio_venta, precio_compra, precio, 0) as precio_venta_final,
                        COALESCE(stock, 0) as stock_final
                    FROM productos 
                    WHERE nombre LIKE ? COLLATE NOCASE
                    ORDER BY id
                """, (f"%{filtro}%",))
            else:
                cur.execute("""
                    SELECT 
                        id,
                        nombre,
                        categoria,
                        COALESCE(unidad_medida, unidad, 'Unitario') as unidad_final,
                        COALESCE(precio_compra, precio, 0) as precio_compra_final,
                        COALESCE(precio_venta, precio_compra, precio, 0) as precio_venta_final,
                        COALESCE(stock, 0) as stock_final
                    FROM productos
                    ORDER BY id
                """)
            
            productos = cur.fetchall()
            print(f"📦 Productos encontrados: {len(productos)}")
            
            for prod in productos:
                # Ahora siempre esperamos exactamente 7 valores de la consulta
                pid, p_nombre, p_cat, p_uni, p_pc, p_pv, p_stock = prod
                
                tabla.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(pid), text_align="center")),
                            ft.DataCell(ft.Text(p_nombre or "Sin nombre", text_align="left")),
                            ft.DataCell(ft.Text(p_cat or "Sin categoría", text_align="center")),
                            ft.DataCell(ft.Text(p_uni or "Unitario", text_align="center")),
                            ft.DataCell(ft.Text(f"Gs. {int(p_pc or 0):,.0f}".replace(',', '.'), text_align="center")),
                            ft.DataCell(ft.Text(f"Gs. {int(p_pv or 0):,.0f}".replace(',', '.'), text_align="center")),
                            ft.DataCell(ft.Text(f"{int(p_stock or 0):,.0f}".replace(',', '.'), text_align="center")),
                        ],
                        on_select_changed=lambda e, pid=pid: seleccionar(pid),
                    )
                )
            
            conn.close()
            print(f"✅ Tabla actualizada con {len(tabla.rows)} productos")
            
        except Exception as e:
            print(f"❌ Error refrescando tabla: {e}")
            error_msg.value = f"❌ Error cargando productos: {str(e)}"
            import traceback
            traceback.print_exc()
        
        page.update()

    def seleccionar(pid):
        """Función corregida para seleccionar productos"""
        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    id,
                    nombre,
                    categoria,
                    COALESCE(unidad_medida, unidad, 'Unitario') as unidad_final,
                    COALESCE(precio_compra, precio, 0) as precio_compra_final,
                    COALESCE(precio_venta, precio_compra, precio, 0) as precio_venta_final,
                    COALESCE(stock, 0) as stock_final
                FROM productos 
                WHERE id=?
            """, (pid,))
            prod = cur.fetchone()
            conn.close()
            
            if prod:
                selected_id["id"] = prod[0]
                producto_original["data"] = prod
                nombre.value = prod[1] or ""
                categoria.value = prod[2] or ""
                unidad.value = prod[3] or "Unitario"
                precio_compra.value = str(int(prod[4] or 0))
                precio_venta.value = str(int(prod[5] or 0))
                stock.value = str(int(prod[6] or 0))
                error_msg.value = ""
                page.update()
                print(f"✅ Producto seleccionado: {prod[1]}")
        except Exception as e:
            print(f"❌ Error seleccionando producto: {e}")
            error_msg.value = f"❌ Error: {str(e)}"
            page.update()

    def editar_producto(e):
        if not selected_id["id"]:
            error_msg.value = "⚠️ Selecciona un producto para editar"
            page.update()
            return
        if not nombre.value or not nombre.value.strip():
            error_msg.value = "⚠️ El nombre es obligatorio"
            page.update()
            return
        if existe_producto(nombre.value, excluir_id=selected_id["id"]):
            error_msg.value = "⚠️ Ya existe un producto con este nombre"
            page.update()
            return
        if not categoria.value or not unidad.value or not precio_compra.value or not precio_venta.value:
            error_msg.value = "⚠️ Todos los campos son obligatorios"
            page.update()
            return
        try:
            pc = float(precio_compra.value.replace(".", "").replace(",", ""))
            pv = float(precio_venta.value.replace(".", "").replace(",", ""))
            st = int(stock.value or "0")
        except:
            error_msg.value = "⚠️ Los precios y stock deben ser válidos"
            page.update()
            return

        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE productos 
                SET nombre=?, categoria=?, unidad_medida=?, precio_compra=?, precio_venta=?, stock=? 
                WHERE id=?
            """, (nombre.value.strip(), categoria.value, unidad.value, pc, pv, st, selected_id["id"]))
            
            conn.commit()
        except sqlite3.IntegrityError:
            error_msg.value = "⚠️ Ya existe un producto con este nombre"
            page.update()
            return
        except Exception as ex:
            error_msg.value = f"⚠️ Error: {str(ex)}"
            page.update()
            return
        finally:
            conn.close()

        limpiar_form()
        refrescar_tabla()
        show_snackbar("✏️ Producto editado correctamente", "#0288D1")

    def eliminar_producto(e):
        if not selected_id["id"]:
            error_msg.value = "⚠️ Selecciona un producto para eliminar"
            page.update()
            return
        
        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("DELETE FROM productos WHERE id=?", (selected_id["id"],))
            conn.commit()
            conn.close()
        except Exception as ex:
            error_msg.value = f"⚠️ Error eliminando: {str(ex)}"
            page.update()
            return
            
        limpiar_form()
        refrescar_tabla()
        show_snackbar("🗑️ Producto eliminado correctamente", "#C62828")

    botones = ft.Row(
        [
            ft.ElevatedButton("Agregar", on_click=agregar_producto, bgcolor=PRIMARY_COLOR, color="white", icon=ft.icons.ADD),
            ft.ElevatedButton("Editar", on_click=editar_producto, bgcolor="#0288D1", color="white", icon=ft.icons.EDIT),
            ft.ElevatedButton("Eliminar", on_click=eliminar_producto, bgcolor="#C62828", color="white", icon=ft.icons.DELETE),
            ft.ElevatedButton("Limpiar", on_click=lambda e: limpiar_form(), bgcolor="#757575", color="white", icon=ft.icons.CLEAR),
        ],
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        spacing=10,
    )

    volver_icon = ft.IconButton(
        icon=ft.icons.ARROW_BACK,
        tooltip="Volver al Dashboard",
        icon_color=PRIMARY_COLOR,
        on_click=lambda e: dashboard.dashboard_view(content, page=page),
    )

    form_card = ft.Container(
        content=ft.Column(
            [
                ft.Row([volver_icon, ft.Text("Gestión de Productos", size=25, weight="bold", color="black")]),
                nombre,
                sugerencias,
                categoria,
                unidad,
                precio_compra,
                precio_venta,
                stock,
                error_msg,
                botones,
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        ),
        width=600,
        padding=30,
        border_radius=20,
        bgcolor=ft.colors.with_opacity(0.7, ft.colors.WHITE),
        shadow=ft.BoxShadow(blur_radius=15, color="#444"),
    )

    tabla_card = ft.Container(
        content=ft.Column(
            [
                busqueda,
                ft.ListView(
                    controls=[
                        ft.Row([tabla], expand=True, scroll=ft.ScrollMode.AUTO)
                    ],
                    expand=True,
                    spacing=0,
                    padding=0,
                    height=400,
                ),
            ],
            expand=True,
        ),
        expand=True,
        padding=20,
        border_radius=20,
        bgcolor=ft.colors.with_opacity(0.7, ft.colors.WHITE),
        shadow=ft.BoxShadow(blur_radius=15, color="#444"),
        width=750,  # Aumentado para la nueva columna
    )

    content.controls.append(
        ft.Row(
            [form_card, tabla_card],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            expand=True,
        )
    )

    refrescar_tabla()

    if page:
        page.update()