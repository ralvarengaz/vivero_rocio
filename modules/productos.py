"""
Módulo de Gestión de Productos
Migrado a nueva arquitectura con PostgreSQL, Config y Utils
"""
import flet as ft
from modules.db_service import db
from modules.config import Colors, FontSizes, Sizes, Messages, Icons, Spacing
from modules.utils import (
    format_guarani, parse_guarani, sanitize_string, to_int
)
from modules.session_service import session
from modules import dashboard


def crud_view(content, page=None):
    """Vista principal de gestión de productos"""
    content.controls.clear()

    # === VARIABLES DE ESTADO ===
    selected_id = {"id": None}

    # === CAMPOS DEL FORMULARIO ===
    nombre = ft.TextField(
        label="Nombre Producto",
        width=Sizes.INPUT_WIDTH_LARGE,
        hint_text="Ej: Rosa Blanca",
        prefix_icon=Icons.PRODUCTOS,
        height=Sizes.INPUT_HEIGHT,
    )

    categoria = ft.Dropdown(
        label="Categoría",
        width=Sizes.INPUT_WIDTH_MEDIUM,
        options=[
            ft.dropdown.Option("Flores"),
            ft.dropdown.Option("Plantas"),
            ft.dropdown.Option("Semillas"),
            ft.dropdown.Option("Herramientas"),
            ft.dropdown.Option("Fertilizantes"),
            ft.dropdown.Option("Macetas"),
            ft.dropdown.Option("Otros"),
        ],
        height=Sizes.INPUT_HEIGHT,
    )

    precio_compra = ft.TextField(
        label="Precio Compra (₲)",
        width=Sizes.INPUT_WIDTH_MEDIUM,
        hint_text="Ej: 10000",
        prefix_icon=ft.icons.ATTACH_MONEY,
        height=Sizes.INPUT_HEIGHT,
    )

    precio_venta = ft.TextField(
        label="Precio Venta (₲)",
        width=Sizes.INPUT_WIDTH_MEDIUM,
        hint_text="Ej: 15000",
        prefix_icon=ft.icons.SELL,
        height=Sizes.INPUT_HEIGHT,
    )

    stock_actual = ft.TextField(
        label="Stock Actual",
        width=Sizes.INPUT_WIDTH_SMALL,
        hint_text="Ej: 50",
        prefix_icon=ft.icons.INVENTORY,
        height=Sizes.INPUT_HEIGHT,
        value="0",
    )

    stock_minimo = ft.TextField(
        label="Stock Mínimo",
        width=Sizes.INPUT_WIDTH_SMALL,
        hint_text="Ej: 10",
        prefix_icon=ft.icons.WARNING,
        height=Sizes.INPUT_HEIGHT,
        value="5",
    )

    descripcion = ft.TextField(
        label="Descripción",
        width=Sizes.INPUT_WIDTH_LARGE,
        hint_text="Descripción del producto",
        prefix_icon=ft.icons.DESCRIPTION,
        height=Sizes.INPUT_HEIGHT,
        multiline=True,
        min_lines=2,
        max_lines=3,
    )

    error_msg = ft.Text("", color=Colors.ERROR, size=FontSizes.NORMAL)

    # === FILTROS ===
    filtro_nombre = ft.TextField(
        label="Buscar por Nombre",
        width=220,
        prefix_icon=Icons.SEARCH,
        height=Sizes.INPUT_HEIGHT,
    )

    filtro_categoria = ft.Dropdown(
        label="Categoría",
        width=180,
        options=[
            ft.dropdown.Option("", "Todas"),
            ft.dropdown.Option("Flores"),
            ft.dropdown.Option("Plantas"),
            ft.dropdown.Option("Semillas"),
            ft.dropdown.Option("Herramientas"),
            ft.dropdown.Option("Fertilizantes"),
            ft.dropdown.Option("Macetas"),
            ft.dropdown.Option("Otros"),
        ],
        value="",
        height=Sizes.INPUT_HEIGHT,
    )

    # === FUNCIONES DE UTILIDAD ===
    def show_snackbar(msg: str, color: str):
        """Muestra mensaje temporal"""
        page.open(ft.SnackBar(
            content=ft.Text(msg, color=Colors.TEXT_WHITE),
            bgcolor=color,
            duration=3000
        ))

    def limpiar_form():
        """Limpia el formulario"""
        nombre.value = ""
        categoria.value = None
        precio_compra.value = ""
        precio_venta.value = ""
        stock_actual.value = "0"
        stock_minimo.value = "5"
        descripcion.value = ""
        selected_id["id"] = None
        error_msg.value = ""
        page.update()

    # === TABLA DE PRODUCTOS ===
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Nombre", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("Categoría", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("P. Compra", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("P. Venta", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("Stock", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("Stock Mín", color=Colors.PRIMARY, weight="bold")),
        ],
        rows=[],
        column_spacing=8,
        heading_row_height=Sizes.TABLE_HEADER_HEIGHT,
    )

    def refrescar_tabla(e=None):
        """Refresca la tabla de productos desde PostgreSQL"""
        tabla.rows.clear()

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                # Query optimizada con columnas específicas y LIMIT
                query = """
                    SELECT id, nombre, categoria, precio_compra, precio_venta,
                           stock_actual, stock_minimo
                    FROM productos
                    WHERE 1=1
                """
                params = []

                # Aplicar filtros
                if filtro_nombre.value.strip():
                    query += " AND LOWER(nombre) LIKE %s"
                    params.append(f"%{filtro_nombre.value.strip().lower()}%")

                if filtro_categoria.value:
                    query += " AND categoria = %s"
                    params.append(filtro_categoria.value)

                query += " ORDER BY id ASC LIMIT 100"

                cur.execute(query, tuple(params))
                rows = cur.fetchall()

                for prod in rows:
                    pid, p_nombre, p_cat, p_compra, p_venta, p_stock, p_stock_min = prod

                    # Determinar color del stock
                    stock_val = p_stock or 0
                    stock_min_val = p_stock_min or 5

                    if stock_val == 0:
                        stock_color = Colors.ERROR
                    elif stock_val <= stock_min_val:
                        stock_color = Colors.WARNING
                    else:
                        stock_color = Colors.SUCCESS

                    stock_container = ft.Container(
                        content=ft.Text(str(stock_val), color=Colors.TEXT_WHITE, weight="bold", size=FontSizes.SMALL),
                        bgcolor=stock_color,
                        padding=ft.padding.symmetric(vertical=4, horizontal=8),
                        border_radius=8,
                    )

                    tabla.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(p_nombre or "", size=FontSizes.NORMAL)),
                                ft.DataCell(ft.Text(p_cat or "", size=FontSizes.NORMAL)),
                                ft.DataCell(ft.Text(format_guarani(p_compra or 0), size=FontSizes.NORMAL)),
                                ft.DataCell(ft.Text(format_guarani(p_venta or 0), size=FontSizes.NORMAL)),
                                ft.DataCell(stock_container),
                                ft.DataCell(ft.Text(str(p_stock_min or 5), size=FontSizes.NORMAL)),
                            ],
                            on_select_changed=lambda e, pid=pid: seleccionar(pid),
                        )
                    )

                print(f"✅ Productos cargados: {len(rows)}")

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_CONNECTION}: {str(ex)}"
            print(f"❌ Error refrescando productos: {ex}")
            show_snackbar(Messages.ERROR_CONNECTION, Colors.ERROR)

        page.update()

    def seleccionar(pid):
        """Selecciona un producto para edición"""
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, nombre, categoria, precio_compra, precio_venta,
                           stock_actual, stock_minimo, descripcion
                    FROM productos WHERE id=%s
                """, (pid,))
                prod = cur.fetchone()

                if prod:
                    selected_id["id"] = prod[0]
                    nombre.value = prod[1] or ""
                    categoria.value = prod[2] or None
                    precio_compra.value = str(prod[3] or 0)
                    precio_venta.value = str(prod[4] or 0)
                    stock_actual.value = str(prod[5] or 0)
                    stock_minimo.value = str(prod[6] or 5)
                    descripcion.value = prod[7] or ""
                    error_msg.value = ""
                    page.update()

        except Exception as ex:
            error_msg.value = f"Error al seleccionar: {str(ex)}"
            print(f"❌ Error seleccionando producto: {ex}")
            page.update()

    def agregar_producto(e):
        """Agrega un nuevo producto con validación completa"""
        errores = []

        # Sanitizar inputs
        nombre_clean = sanitize_string(nombre.value)

        # Validaciones
        if not nombre_clean:
            errores.append("El campo Nombre es obligatorio.")

        if not categoria.value:
            errores.append("Debes seleccionar una categoría.")

        # Validar precios
        try:
            p_compra = parse_guarani(precio_compra.value) if precio_compra.value.strip() else 0
            if p_compra < 0:
                errores.append("El precio de compra debe ser mayor o igual a 0.")
        except:
            errores.append("El precio de compra debe ser un número válido.")
            p_compra = 0

        try:
            p_venta = parse_guarani(precio_venta.value) if precio_venta.value.strip() else 0
            if p_venta < 0:
                errores.append("El precio de venta debe ser mayor o igual a 0.")
        except:
            errores.append("El precio de venta debe ser un número válido.")
            p_venta = 0

        # Validar stocks
        try:
            s_actual = to_int(stock_actual.value)
            if s_actual < 0:
                errores.append("El stock actual no puede ser negativo.")
        except:
            errores.append("El stock actual debe ser un número entero.")
            s_actual = 0

        try:
            s_minimo = to_int(stock_minimo.value)
            if s_minimo < 0:
                errores.append("El stock mínimo no puede ser negativo.")
        except:
            errores.append("El stock mínimo debe ser un número entero.")
            s_minimo = 5

        if errores:
            error_msg.value = Messages.WARNING_EMPTY_FIELDS + " " + " ".join(errores)
            page.update()
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                # Insertar producto
                cur.execute("""
                    INSERT INTO productos
                    (nombre, categoria, precio_compra, precio_venta, stock_actual, stock_minimo, descripcion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    nombre_clean,
                    categoria.value,
                    p_compra,
                    p_venta,
                    s_actual,
                    s_minimo,
                    descripcion.value.strip() or None
                ))

                conn.commit()

                limpiar_form()
                refrescar_tabla()
                show_snackbar(Messages.SUCCESS_CREATE, Colors.SUCCESS)

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_CREATE}: {str(ex)}"
            print(f"❌ Error agregando producto: {ex}")
            show_snackbar(Messages.ERROR_CREATE, Colors.ERROR)
            page.update()

    def editar_producto(e):
        """Edita un producto existente con validación"""
        if not selected_id["id"]:
            error_msg.value = "Selecciona un producto para editar."
            page.update()
            return

        errores = []

        # Sanitizar inputs
        nombre_clean = sanitize_string(nombre.value)

        # Validaciones
        if not nombre_clean:
            errores.append("El campo Nombre es obligatorio.")

        if not categoria.value:
            errores.append("Debes seleccionar una categoría.")

        # Validar precios
        try:
            p_compra = parse_guarani(precio_compra.value) if precio_compra.value.strip() else 0
            if p_compra < 0:
                errores.append("El precio de compra debe ser mayor o igual a 0.")
        except:
            errores.append("El precio de compra debe ser un número válido.")
            p_compra = 0

        try:
            p_venta = parse_guarani(precio_venta.value) if precio_venta.value.strip() else 0
            if p_venta < 0:
                errores.append("El precio de venta debe ser mayor o igual a 0.")
        except:
            errores.append("El precio de venta debe ser un número válido.")
            p_venta = 0

        # Validar stocks
        try:
            s_actual = to_int(stock_actual.value)
            if s_actual < 0:
                errores.append("El stock actual no puede ser negativo.")
        except:
            errores.append("El stock actual debe ser un número entero.")
            s_actual = 0

        try:
            s_minimo = to_int(stock_minimo.value)
            if s_minimo < 0:
                errores.append("El stock mínimo no puede ser negativo.")
        except:
            errores.append("El stock mínimo debe ser un número entero.")
            s_minimo = 5

        if errores:
            error_msg.value = Messages.WARNING_EMPTY_FIELDS + " " + " ".join(errores)
            page.update()
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                # Actualizar producto
                cur.execute("""
                    UPDATE productos
                    SET nombre=%s, categoria=%s, precio_compra=%s, precio_venta=%s,
                        stock_actual=%s, stock_minimo=%s, descripcion=%s
                    WHERE id=%s
                """, (
                    nombre_clean,
                    categoria.value,
                    p_compra,
                    p_venta,
                    s_actual,
                    s_minimo,
                    descripcion.value.strip() or None,
                    selected_id["id"]
                ))

                conn.commit()

                limpiar_form()
                refrescar_tabla()
                show_snackbar(Messages.SUCCESS_UPDATE, Colors.INFO)

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_UPDATE}: {str(ex)}"
            print(f"❌ Error editando producto: {ex}")
            show_snackbar(Messages.ERROR_UPDATE, Colors.ERROR)
            page.update()

    def eliminar_producto(e):
        """Elimina un producto con confirmación"""
        if not selected_id["id"]:
            error_msg.value = "Selecciona un producto para eliminar."
            page.update()
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM productos WHERE id=%s", (selected_id["id"],))
                conn.commit()

                limpiar_form()
                refrescar_tabla()
                show_snackbar("Producto eliminado correctamente", Colors.ERROR)

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_DELETE}: {str(ex)}"
            print(f"❌ Error eliminando producto: {ex}")
            show_snackbar(Messages.ERROR_DELETE, Colors.ERROR)
            page.update()

    # === BOTONES DE ACCIÓN ===
    botones = ft.Row(
        [
            ft.ElevatedButton(
                "Agregar",
                on_click=agregar_producto,
                bgcolor=Colors.SUCCESS,
                color=Colors.TEXT_WHITE,
                icon=Icons.ADD,
                height=Sizes.BUTTON_HEIGHT,
            ),
            ft.ElevatedButton(
                "Editar",
                on_click=editar_producto,
                bgcolor=Colors.INFO,
                color=Colors.TEXT_WHITE,
                icon=Icons.EDIT,
                height=Sizes.BUTTON_HEIGHT,
            ),
            ft.ElevatedButton(
                "Eliminar",
                on_click=eliminar_producto,
                bgcolor=Colors.ERROR,
                color=Colors.TEXT_WHITE,
                icon=Icons.DELETE,
                height=Sizes.BUTTON_HEIGHT,
            ),
            ft.ElevatedButton(
                "Limpiar",
                on_click=lambda e: limpiar_form(),
                bgcolor=Colors.TEXT_DISABLED,
                color=Colors.TEXT_WHITE,
                icon=Icons.CANCEL,
                height=Sizes.BUTTON_HEIGHT,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        spacing=Spacing.MEDIUM,
    )

    volver_icon = ft.IconButton(
        icon=Icons.BACK,
        tooltip="Volver al Dashboard",
        icon_color=Colors.PRIMARY,
        on_click=lambda e: dashboard.dashboard_view(content, page=page),
        bgcolor=ft.colors.with_opacity(0.1, Colors.PRIMARY),
    )

    # === TARJETA DEL FORMULARIO ===
    form_card = ft.Container(
        content=ft.Column(
            [
                ft.Row([volver_icon, ft.Text("Gestión de Productos", size=FontSizes.XLARGE, weight="bold", color=Colors.PRIMARY)]),
                nombre,
                categoria,
                ft.Row([precio_compra, precio_venta], spacing=Spacing.MEDIUM),
                ft.Row([stock_actual, stock_minimo], spacing=Spacing.MEDIUM),
                descripcion,
                error_msg,
                botones,
            ],
            spacing=Spacing.MEDIUM,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            scroll=ft.ScrollMode.AUTO,
        ),
        width=500,
        height=650,
        padding=Sizes.CARD_PADDING,
        border_radius=Sizes.CARD_RADIUS,
        bgcolor=Colors.CARD_BG,
        shadow=ft.BoxShadow(blur_radius=12, color=ft.colors.with_opacity(0.2, Colors.TEXT_PRIMARY)),
    )

    # === TARJETA DE FILTROS ===
    filtros_card = ft.Container(
        content=ft.Row([filtro_nombre, filtro_categoria], spacing=Spacing.MEDIUM),
        padding=Spacing.MEDIUM,
        border_radius=Sizes.CARD_RADIUS,
        bgcolor=ft.colors.with_opacity(0.5, Colors.BG_WHITE),
    )

    # === TARJETA DE TABLA CON SCROLL ===
    tabla_card = ft.Container(
        content=ft.Column([
            filtros_card,
            ft.Container(
                content=ft.Column(
                    [tabla],
                    scroll=ft.ScrollMode.AUTO,
                    auto_scroll=True,
                ),
                height=600,
                border=ft.border.all(1, Colors.BORDER_LIGHT),
                border_radius=Sizes.CARD_RADIUS,
                padding=Spacing.NORMAL,
            ),
        ], expand=True, spacing=Spacing.MEDIUM),
        expand=True,
        padding=Sizes.CARD_PADDING,
        border_radius=Sizes.CARD_RADIUS,
        bgcolor=Colors.CARD_BG,
        shadow=ft.BoxShadow(blur_radius=12, color=ft.colors.with_opacity(0.2, Colors.TEXT_PRIMARY)),
        width=750,
    )

    # === LAYOUT PRINCIPAL ===
    content.controls.append(
        ft.Row(
            [form_card, tabla_card],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            expand=True
        )
    )

    # === EVENTOS ===
    filtro_nombre.on_change = refrescar_tabla
    filtro_categoria.on_change = refrescar_tabla

    # === CARGA INICIAL ===
    refrescar_tabla()

    if page:
        page.update()

    print("✅ Módulo de Productos cargado (PostgreSQL + Nueva Arquitectura)")
