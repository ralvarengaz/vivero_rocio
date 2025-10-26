"""
Módulo de Gestión de Proveedores
Migrado a nueva arquitectura con PostgreSQL, Config y Utils
"""
import flet as ft
from modules.db_service import db
from modules.config import Colors, FontSizes, Sizes, Messages, Icons, Spacing
from modules.utils import (
    format_guarani, parse_guarani, validate_email, validate_phone,
    validate_ruc, open_whatsapp, sanitize_string
)
from modules.session_service import session
from modules import dashboard


def crud_view(content, page=None):
    """Vista principal de gestión de proveedores"""
    content.controls.clear()

    # === VARIABLES DE ESTADO ===
    selected_id = {"id": None}

    # === CAMPOS DEL FORMULARIO ===
    nombre = ft.TextField(
        label="Nombre Proveedor",
        width=Sizes.INPUT_WIDTH_LARGE,
        hint_text="Ej: Vivero Central S.A.",
        prefix_icon=Icons.PROVEEDORES,
        height=Sizes.INPUT_HEIGHT,
    )

    ruc = ft.TextField(
        label="RUC",
        width=Sizes.INPUT_WIDTH_MEDIUM,
        hint_text="Ej: 80012345-6",
        prefix_icon=ft.icons.BADGE,
        height=Sizes.INPUT_HEIGHT,
    )

    direccion = ft.TextField(
        label="Dirección",
        width=Sizes.INPUT_WIDTH_LARGE,
        hint_text="Dirección completa",
        prefix_icon=ft.icons.LOCATION_ON,
        height=Sizes.INPUT_HEIGHT,
    )

    telefono = ft.TextField(
        label="Teléfono",
        width=220,
        hint_text="Ej: 0981123456",
        prefix_icon=Icons.PHONE,
        height=Sizes.INPUT_HEIGHT,
    )

    email = ft.TextField(
        label="Correo electrónico",
        width=Sizes.INPUT_WIDTH_LARGE,
        hint_text="Ej: proveedor@email.com",
        prefix_icon=Icons.EMAIL,
        height=Sizes.INPUT_HEIGHT,
    )

    contacto_principal = ft.TextField(
        label="Contacto Principal",
        width=Sizes.INPUT_WIDTH_LARGE,
        hint_text="Nombre del contacto",
        prefix_icon=ft.icons.PERSON,
        height=Sizes.INPUT_HEIGHT,
    )

    observaciones = ft.TextField(
        label="Observaciones",
        width=Sizes.INPUT_WIDTH_LARGE,
        hint_text="Notas adicionales",
        prefix_icon=ft.icons.NOTES,
        height=Sizes.INPUT_HEIGHT,
        multiline=True,
        min_lines=2,
        max_lines=4,
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
        direccion.value = ""
        telefono.value = ""
        email.value = ""
        contacto_principal.value = ""
        observaciones.value = ""
        selected_id["id"] = None
        error_msg.value = ""
        page.update()

    def abrir_whatsapp_form(e):
        """Abre WhatsApp del proveedor en el formulario"""
        if telefono.value.strip():
            nombre_proveedor = nombre.value or contacto_principal.value or "proveedor"
            if open_whatsapp(telefono.value, nombre_proveedor):
                show_snackbar(f"Abriendo WhatsApp de {nombre_proveedor}", Colors.SUCCESS)
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

    # === TABLA DE PROVEEDORES ===
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Nombre", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("RUC", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("Teléfono", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("Email", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("Contacto", color=Colors.PRIMARY, weight="bold")),
            ft.DataColumn(ft.Text("WhatsApp", color=Colors.PRIMARY, weight="bold")),
        ],
        rows=[],
        column_spacing=8,
        heading_row_height=Sizes.TABLE_HEADER_HEIGHT,
    )

    def refrescar_tabla(e=None):
        """Refresca la tabla de proveedores desde PostgreSQL"""
        tabla.rows.clear()

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                # Query optimizada con columnas específicas y LIMIT
                query = """
                    SELECT id, nombre, ruc, telefono, email, contacto_principal
                    FROM proveedores
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

                for prov in rows:
                    pid, p_nombre, p_ruc, p_tel, p_email, p_contacto = prov

                    # Handler para WhatsApp con closure correcta
                    def crear_handler_whatsapp(num, nom):
                        def handler(e):
                            if open_whatsapp(num, nom):
                                show_snackbar(f"Abriendo WhatsApp de {nom}", Colors.SUCCESS)
                            else:
                                show_snackbar(Messages.WARNING_INVALID_PHONE, Colors.WARNING)
                        return handler

                    tabla.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(p_nombre or "", size=FontSizes.NORMAL)),
                                ft.DataCell(ft.Text(p_ruc or "", size=FontSizes.NORMAL)),
                                ft.DataCell(ft.Text(p_tel or "", size=FontSizes.NORMAL)),
                                ft.DataCell(ft.Text(p_email or "", size=FontSizes.NORMAL)),
                                ft.DataCell(ft.Text(p_contacto or "", size=FontSizes.NORMAL)),
                                ft.DataCell(
                                    ft.IconButton(
                                        icon=Icons.WHATSAPP,
                                        icon_color="#25D366",
                                        tooltip=f"Contactar a {p_nombre or 'proveedor'}",
                                        on_click=crear_handler_whatsapp(p_tel, p_nombre),
                                    )
                                ),
                            ],
                            on_select_changed=lambda e, pid=pid: seleccionar(pid),
                        )
                    )

                print(f"✅ Proveedores cargados: {len(rows)}")

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_CONNECTION}: {str(ex)}"
            print(f"❌ Error refrescando proveedores: {ex}")
            show_snackbar(Messages.ERROR_CONNECTION, Colors.ERROR)

        page.update()

    def seleccionar(pid):
        """Selecciona un proveedor para edición"""
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, nombre, ruc, direccion, telefono, email,
                           contacto_principal, observaciones
                    FROM proveedores WHERE id=%s
                """, (pid,))
                prov = cur.fetchone()

                if prov:
                    selected_id["id"] = prov[0]
                    nombre.value = prov[1] or ""
                    ruc.value = prov[2] or ""
                    direccion.value = prov[3] or ""
                    telefono.value = prov[4] or ""
                    email.value = prov[5] or ""
                    contacto_principal.value = prov[6] or ""
                    observaciones.value = prov[7] or ""
                    error_msg.value = ""
                    page.update()

        except Exception as ex:
            error_msg.value = f"Error al seleccionar: {str(ex)}"
            print(f"❌ Error seleccionando proveedor: {ex}")
            page.update()

    def agregar_proveedor(e):
        """Agrega un nuevo proveedor con validación completa"""
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

        if email.value.strip() and not validate_email(email.value.strip()):
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
                cur.execute("SELECT id FROM proveedores WHERE ruc=%s", (ruc_clean,))
                if cur.fetchone():
                    error_msg.value = f"Ya existe un proveedor con el RUC {ruc_clean}."
                    page.update()
                    return

                # Insertar proveedor
                cur.execute("""
                    INSERT INTO proveedores
                    (nombre, ruc, direccion, telefono, email, contacto_principal, observaciones)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    nombre_clean,
                    ruc_clean,
                    direccion.value.strip() or None,
                    telefono.value.strip() or None,
                    email.value.strip() or None,
                    contacto_principal.value.strip() or None,
                    observaciones.value.strip() or None
                ))

                conn.commit()

                limpiar_form()
                refrescar_tabla()
                show_snackbar(Messages.SUCCESS_CREATE, Colors.SUCCESS)

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_CREATE}: {str(ex)}"
            print(f"❌ Error agregando proveedor: {ex}")
            show_snackbar(Messages.ERROR_CREATE, Colors.ERROR)
            page.update()

    def editar_proveedor(e):
        """Edita un proveedor existente con validación"""
        if not selected_id["id"]:
            error_msg.value = "Selecciona un proveedor para editar."
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

        if email.value.strip() and not validate_email(email.value.strip()):
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
                    "SELECT id FROM proveedores WHERE ruc=%s AND id!=%s",
                    (ruc_clean, selected_id["id"])
                )
                if cur.fetchone():
                    error_msg.value = f"Ya existe un proveedor con el RUC {ruc_clean}."
                    page.update()
                    return

                # Actualizar proveedor
                cur.execute("""
                    UPDATE proveedores
                    SET nombre=%s, ruc=%s, direccion=%s, telefono=%s,
                        email=%s, contacto_principal=%s, observaciones=%s
                    WHERE id=%s
                """, (
                    nombre_clean,
                    ruc_clean,
                    direccion.value.strip() or None,
                    telefono.value.strip() or None,
                    email.value.strip() or None,
                    contacto_principal.value.strip() or None,
                    observaciones.value.strip() or None,
                    selected_id["id"]
                ))

                conn.commit()

                limpiar_form()
                refrescar_tabla()
                show_snackbar(Messages.SUCCESS_UPDATE, Colors.INFO)

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_UPDATE}: {str(ex)}"
            print(f"❌ Error editando proveedor: {ex}")
            show_snackbar(Messages.ERROR_UPDATE, Colors.ERROR)
            page.update()

    def eliminar_proveedor(e):
        """Elimina un proveedor con confirmación"""
        if not selected_id["id"]:
            error_msg.value = "Selecciona un proveedor para eliminar."
            page.update()
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM proveedores WHERE id=%s", (selected_id["id"],))
                conn.commit()

                limpiar_form()
                refrescar_tabla()
                show_snackbar("Proveedor eliminado correctamente", Colors.ERROR)

        except Exception as ex:
            error_msg.value = f"{Messages.ERROR_DELETE}: {str(ex)}"
            print(f"❌ Error eliminando proveedor: {ex}")
            show_snackbar(Messages.ERROR_DELETE, Colors.ERROR)
            page.update()

    # === BOTONES DE ACCIÓN ===
    botones = ft.Row(
        [
            ft.ElevatedButton(
                "Agregar",
                on_click=agregar_proveedor,
                bgcolor=Colors.SUCCESS,
                color=Colors.TEXT_WHITE,
                icon=Icons.ADD,
                height=Sizes.BUTTON_HEIGHT,
            ),
            ft.ElevatedButton(
                "Editar",
                on_click=editar_proveedor,
                bgcolor=Colors.INFO,
                color=Colors.TEXT_WHITE,
                icon=Icons.EDIT,
                height=Sizes.BUTTON_HEIGHT,
            ),
            ft.ElevatedButton(
                "Eliminar",
                on_click=eliminar_proveedor,
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
                ft.Row([volver_icon, ft.Text("Gestión de Proveedores", size=FontSizes.XLARGE, weight="bold", color=Colors.PRIMARY)]),
                nombre,
                ruc,
                direccion,
                telefono_row,
                email,
                contacto_principal,
                observaciones,
                error_msg,
                botones,
            ],
            spacing=Spacing.MEDIUM,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            scroll=ft.ScrollMode.AUTO,
        ),
        width=500,
        height=700,
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
    filtro_ruc.on_change = refrescar_tabla

    # === CARGA INICIAL ===
    refrescar_tabla()

    if page:
        page.update()

    print("✅ Módulo de Proveedores cargado (PostgreSQL + Nueva Arquitectura)")
