"""
Módulo de Gestión de Clientes
Migrado a nueva arquitectura con PostgreSQL, Config y Utils
"""
import flet as ft
from modules.db_service import db
from modules.config import Colors, FontSizes, Sizes, Messages, Icons, Spacing
from modules.utils import (
    format_guarani, parse_guarani, validate_email, validate_phone,
    validate_ruc, open_whatsapp, sanitize_string, normalize_phone
)
from modules.session_service import session
from modules import dashboard
from modules.ciudades_paraguay import CIUDADES_PARAGUAY


def crud_view(content, page=None):
    """Vista principal de gestión de clientes"""
    content.controls.clear()

    # === VARIABLES DE ESTADO ===
    selected_id = {"id": None}

    # === CAMPOS DEL FORMULARIO ===
    nombre = ft.TextField(
        label="Nombre",
        width=Sizes.INPUT_WIDTH_LARGE,
        hint_text="Ej: Juan Pérez",
        prefix_icon=Icons.CLIENTES,
        height=Sizes.INPUT_HEIGHT,
    )

    ruc = ft.TextField(
        label="RUC",
        width=Sizes.INPUT_WIDTH_MEDIUM,
        hint_text="Ej: 1234567-8",
        prefix_icon=ft.icons.BADGE,
        height=Sizes.INPUT_HEIGHT,
    )

    ciudad = ft.TextField(
        label="Ciudad",
        width=Sizes.INPUT_WIDTH_LARGE,
        hint_text="Buscar ciudad...",
        prefix_icon=ft.icons.LOCATION_CITY,
        height=Sizes.INPUT_HEIGHT,
    )

    sugerencias_ciudad = ft.Column(visible=False, spacing=Spacing.SMALL)

    ubicacion = ft.TextField(
        label="Ubicación",
        width=Sizes.INPUT_WIDTH_LARGE,
        hint_text="Dirección o coordenadas",
        prefix_icon=ft.icons.MAP,
        height=Sizes.INPUT_HEIGHT,
    )

    telefono = ft.TextField(
        label="Teléfono",
        width=220,
        hint_text="Ej: 0981123456",
        prefix_icon=Icons.PHONE,
        height=Sizes.INPUT_HEIGHT,
    )

    correo = ft.TextField(
        label="Correo electrónico",
        width=Sizes.INPUT_WIDTH_LARGE,
        hint_text="Ej: usuario@email.com",
        prefix_icon=Icons.EMAIL,
        height=Sizes.INPUT_HEIGHT,
    )

    error_msg = ft.Text("", color=Colors.ERROR, size=FontSizes.NORMAL)

    # === FILTROS ===
    filtro_nombre = ft.TextField(
        label="Buscar por Nombre",
        width=250,
        prefix_icon=Icons.SEARCH,
        height=Sizes.INPUT_HEIGHT,
    )

    filtro_ruc = ft.TextField(
        label="Buscar por RUC",
        width=250,
        prefix_icon=Icons.SEARCH,
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
        ruc.value = ""
        ciudad.value = ""
        ubicacion.value = ""
        telefono.value = ""
        correo.value = ""
        sugerencias_ciudad.visible = False
        selected_id["id"] = None
        error_msg.value = ""
        page.update()

    def buscar_ciudad(e):
        """Busca ciudades del Paraguay"""
        sugerencias_ciudad.controls.clear()
        texto = ciudad.value.strip().lower()

        if texto:
            resultados = [c for c in CIUDADES_PARAGUAY if texto in c.lower()][:5]
            for r in resultados:
                sugerencias_ciudad.controls.append(
                    ft.TextButton(
                        r,
                        on_click=lambda ev, val=r: seleccionar_ciudad(val),
                        style=ft.ButtonStyle(color=Colors.PRIMARY)
                    )
                )
            sugerencias_ciudad.visible = True if resultados else False
        else:
            sugerencias_ciudad.visible = False
        page.update()

    def seleccionar_ciudad(val):
        """Selecciona una ciudad de las sugerencias"""
        ciudad.value = val
        sugerencias_ciudad.visible = False
        page.update()

    def abrir_whatsapp_form(e):
        """Abre WhatsApp del cliente en el formulario"""
        if telefono.value.strip():
            nombre_cliente = nombre.value or "cliente"
            if open_whatsapp(telefono.value, nombre_cliente):
                show_snackbar(f"Abriendo WhatsApp de {nombre_cliente}", Colors.SUCCESS)
            else:
                show_snackbar(Messages.WARNING_INVALID_PHONE, Colors.WARNING)
        else:
            show_snackbar(Messages.WARNING_INVALID_PHONE, Colors.WARNING)

    telefono_row = ft.Row(
        [
            telefono,
            ft.IconButton(
                icon=Icons.WHATSAPP,
                icon_color="#25D366",
                tooltip="Contactar por WhatsApp",
                on_click=abrir_whatsapp_form,
                bgcolor=ft.colors.with_opacity(0.1, "#25D366"),
            ),
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=Spacing.SMALL,
    )

    # === TABLA DE CLIENTES ===
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Nombre", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("RUC", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("Teléfono", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("WhatsApp", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("Ubicación", color=Colors.PRIMARY, weight="bold")),
        ],
        rows=[],
        column_spacing=8,
        heading_row_height=Sizes.TABLE_HEADER_HEIGHT,
    )

    def refrescar_tabla(e=None):
        """Refresca la tabla de clientes desde PostgreSQL"""
        tabla.rows.clear()

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                # Query optimizada con columnas específicas y LIMIT
                query = """
                    SELECT id, nombre, ruc, telefono, ciudad, ubicacion, correo
                    FROM clientes
                    WHERE 1=1
                """
                params = []

                # Aplicar filtros
                if filtro_nombre.value.strip():
                    query += " AND LOWER(nombre) LIKE %s"
                    params.append(f"%{filtro_nombre.value.strip().lower()}%")

                if filtro_ruc.value.strip():
                    query += " AND ruc LIKE %s"
                    params.append(f"%{filtro_ruc.value.strip()}%")

                query += " ORDER BY id ASC LIMIT 100"

                cur.execute(query, tuple(params))
                rows = cur.fetchall()

                for cli in rows:
                    cid, c_nombre, c_ruc, c_tel, c_ciudad, c_ubicacion, c_correo = cli

                    # Handler para WhatsApp con closure correcta
                    def crear_handler_whatsapp(num, nom):
                        def handler(e):
                            if open_whatsapp(num, nom):
                                show_snackbar(f"Abriendo WhatsApp de {nom}", Colors.SUCCESS)
                            else:
                                show_snackbar(Messages.WARNING_INVALID_PHONE, Colors.WARNING)
                        return handler

                    # Handler para mapa con closure correcta
                    def crear_handler_mapa(destino):
                        def handler(e):
                            if destino:
                                import webbrowser
                                url = f"https://www.google.com/maps/search/?api=1&query={destino}"
                                webbrowser.open(url)
                                show_snackbar(f"Abriendo mapa: {destino[:20]}...", Colors.INFO)
                        return handler

                    tabla.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(c_nombre or "", size=FontSizes.NORMAL)),
                                ft.DataCell(ft.Text(c_ruc or "", size=FontSizes.NORMAL)),
                                ft.DataCell(ft.Text(c_tel or "", size=FontSizes.NORMAL)),
                                ft.DataCell(
                                    ft.IconButton(
                                        icon=Icons.WHATSAPP,
                                        icon_color="#25D366",
                                        tooltip=f"Contactar a {c_nombre or 'cliente'}",
                                        on_click=crear_handler_whatsapp(c_tel, c_nombre),
                                    )
                                ),
                                ft.DataCell(
                                    ft.IconButton(
                                        icon=ft.icons.MAP,
                                        icon_color=Colors.PRIMARY,
                                        tooltip="Ver ubicación",
                                        on_click=crear_handler_mapa(c_ubicacion),
                                    )
                                ),
                            ],
                            on_select_changed=lambda e, cid=cid: seleccionar(cid),
                        )
                    )

                print(f"✅ Clientes cargados: {len(rows)}")

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_CONNECTION}: {str(ex)}"
            print(f"❌ Error refrescando clientes: {ex}")
            show_snackbar(Messages.ERROR_CONNECTION, Colors.ERROR)

        page.update()

    def seleccionar(cid):
        """Selecciona un cliente para edición"""
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, nombre, ruc, telefono, ciudad, ubicacion, correo
                    FROM clientes WHERE id=%s
                """, (cid,))
                cli = cur.fetchone()

                if cli:
                    selected_id["id"] = cli[0]
                    nombre.value = cli[1] or ""
                    ruc.value = cli[2] or ""
                    telefono.value = cli[3] or ""
                    ciudad.value = cli[4] or ""
                    ubicacion.value = cli[5] or ""
                    correo.value = cli[6] or ""
                    error_msg.value = ""
                    page.update()

        except Exception as ex:
            error_msg.value = f"Error al seleccionar: {str(ex)}"
            print(f"❌ Error seleccionando cliente: {ex}")
            page.update()

    def agregar_cliente(e):
        """Agrega un nuevo cliente con validación completa"""
        errores = []

        # Sanitizar inputs
        nombre_clean = sanitize_string(nombre.value)
        ruc_clean = sanitize_string(ruc.value)

        # Validaciones
        if not nombre_clean:
            errores.append("El campo Nombre es obligatorio.")

        if not ruc_clean:
            errores.append("El campo RUC es obligatorio.")
        elif not validate_ruc(ruc_clean):
            errores.append(Messages.WARNING_INVALID_RUC)

        if correo.value.strip() and not validate_email(correo.value.strip()):
            errores.append(Messages.WARNING_INVALID_EMAIL)

        if telefono.value.strip() and not validate_phone(telefono.value.strip()):
            errores.append(Messages.WARNING_INVALID_PHONE)

        if errores:
            error_msg.value = Messages.WARNING_EMPTY_FIELDS + " " + " ".join(errores)
            page.update()
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                # Verificar RUC duplicado
                cur.execute("SELECT id FROM clientes WHERE ruc=%s", (ruc_clean,))
                if cur.fetchone():
                    error_msg.value = f"Ya existe un cliente con el RUC {ruc_clean}."
                    page.update()
                    return

                # Insertar cliente
                cur.execute("""
                    INSERT INTO clientes (nombre, ruc, telefono, ciudad, ubicacion, correo)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    nombre_clean,
                    ruc_clean,
                    telefono.value.strip() or None,
                    ciudad.value.strip() or None,
                    ubicacion.value.strip() or None,
                    correo.value.strip() or None
                ))

                conn.commit()

                limpiar_form()
                refrescar_tabla()
                show_snackbar(Messages.SUCCESS_CREATE, Colors.SUCCESS)

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_CREATE}: {str(ex)}"
            print(f"❌ Error agregando cliente: {ex}")
            show_snackbar(Messages.ERROR_CREATE, Colors.ERROR)
            page.update()

    def editar_cliente(e):
        """Edita un cliente existente con validación"""
        if not selected_id["id"]:
            error_msg.value = "Selecciona un cliente para editar."
            page.update()
            return

        errores = []

        # Sanitizar inputs
        nombre_clean = sanitize_string(nombre.value)
        ruc_clean = sanitize_string(ruc.value)

        # Validaciones
        if not nombre_clean:
            errores.append("El campo Nombre es obligatorio.")

        if not ruc_clean:
            errores.append("El campo RUC es obligatorio.")
        elif not validate_ruc(ruc_clean):
            errores.append(Messages.WARNING_INVALID_RUC)

        if correo.value.strip() and not validate_email(correo.value.strip()):
            errores.append(Messages.WARNING_INVALID_EMAIL)

        if telefono.value.strip() and not validate_phone(telefono.value.strip()):
            errores.append(Messages.WARNING_INVALID_PHONE)

        if errores:
            error_msg.value = Messages.WARNING_EMPTY_FIELDS + " " + " ".join(errores)
            page.update()
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                # Verificar RUC duplicado (excluyendo el registro actual)
                cur.execute(
                    "SELECT id FROM clientes WHERE ruc=%s AND id!=%s",
                    (ruc_clean, selected_id["id"])
                )
                if cur.fetchone():
                    error_msg.value = f"Ya existe un cliente con el RUC {ruc_clean}."
                    page.update()
                    return

                # Actualizar cliente
                cur.execute("""
                    UPDATE clientes
                    SET nombre=%s, ruc=%s, telefono=%s, ciudad=%s, ubicacion=%s, correo=%s
                    WHERE id=%s
                """, (
                    nombre_clean,
                    ruc_clean,
                    telefono.value.strip() or None,
                    ciudad.value.strip() or None,
                    ubicacion.value.strip() or None,
                    correo.value.strip() or None,
                    selected_id["id"]
                ))

                conn.commit()

                limpiar_form()
                refrescar_tabla()
                show_snackbar(Messages.SUCCESS_UPDATE, Colors.INFO)

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_UPDATE}: {str(ex)}"
            print(f"❌ Error editando cliente: {ex}")
            show_snackbar(Messages.ERROR_UPDATE, Colors.ERROR)
            page.update()

    def eliminar_cliente(e):
        """Elimina un cliente con confirmación"""
        if not selected_id["id"]:
            error_msg.value = "Selecciona un cliente para eliminar."
            page.update()
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM clientes WHERE id=%s", (selected_id["id"],))
                conn.commit()

                limpiar_form()
                refrescar_tabla()
                show_snackbar("Cliente eliminado correctamente", Colors.ERROR)

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_DELETE}: {str(ex)}"
            print(f"❌ Error eliminando cliente: {ex}")
            show_snackbar(Messages.ERROR_DELETE, Colors.ERROR)
            page.update()

    # === BOTONES DE ACCIÓN ===
    botones = ft.Row(
        [
            ft.ElevatedButton(
                "Agregar",
                on_click=agregar_cliente,
                bgcolor=Colors.SUCCESS,
                color=Colors.TEXT_WHITE,
                icon=Icons.ADD,
                height=Sizes.BUTTON_HEIGHT,
            ),
            ft.ElevatedButton(
                "Editar",
                on_click=editar_cliente,
                bgcolor=Colors.INFO,
                color=Colors.TEXT_WHITE,
                icon=Icons.EDIT,
                height=Sizes.BUTTON_HEIGHT,
            ),
            ft.ElevatedButton(
                "Eliminar",
                on_click=eliminar_cliente,
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
                ft.Row([volver_icon, ft.Text("Gestión de Clientes", size=FontSizes.XLARGE, weight="bold", color=Colors.PRIMARY)]),
                nombre,
                ruc,
                ciudad,
                sugerencias_ciudad,
                ubicacion,
                telefono_row,
                correo,
                error_msg,
                botones,
            ],
            spacing=Spacing.MEDIUM,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        ),
        width=500,
        padding=Sizes.CARD_PADDING,
        border_radius=Sizes.CARD_RADIUS,
        bgcolor=Colors.CARD_BG,
        shadow=ft.BoxShadow(blur_radius=12, color=ft.colors.with_opacity(0.2, Colors.TEXT_PRIMARY)),
    )

    # === TARJETA DE FILTROS ===
    filtros_card = ft.Container(
        content=ft.Row([filtro_nombre, filtro_ruc], spacing=Spacing.MEDIUM),
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
        width=650,
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
    ciudad.on_change = buscar_ciudad
    filtro_nombre.on_change = refrescar_tabla
    filtro_ruc.on_change = refrescar_tabla

    # === CARGA INICIAL ===
    refrescar_tabla()

    if page:
        page.update()

    print("✅ Módulo de Clientes cargado (PostgreSQL + Nueva Arquitectura)")
