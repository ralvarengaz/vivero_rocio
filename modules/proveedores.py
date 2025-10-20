import flet as ft
import sqlite3
import webbrowser
from modules import dashboard

DB = "data/vivero.db"
PRIMARY_COLOR = "#2E7D32"
ACCENT_COLOR = "#66BB6A"

def crud_view(content, page=None):
    content.controls.clear()

    # --- Barra de mensajes
    def show_snackbar(msg, color):
        page.open(ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color, duration=3000))

    # --- Campos del formulario ---
    nombre = ft.TextField(label="Nombre", width=300, hint_text="Ej: Vivero Central", prefix_icon=ft.icons.PERSON)
    telefono = ft.TextField(label="Teléfono", width=220, hint_text="Ej: 0981123456", prefix_icon=ft.icons.PHONE)
    correo = ft.TextField(label="Correo", width=300, hint_text="Ej: proveedor@email.com", prefix_icon=ft.icons.EMAIL)
    direccion = ft.TextField(label="Dirección", width=300, hint_text="Ej: Calle Falsa 123", prefix_icon=ft.icons.HOME)
    ruc = ft.TextField(label="RUC", width=300, hint_text="Ej: 1234567-8", prefix_icon=ft.icons.BADGE)

    error_msg = ft.Text("", color="red")

    selected_id = {"id": None}
    proveedor_original = {"data": None}

    # --- Función WhatsApp ---
    def abrir_whatsapp_numero(numero, nombre_prov="proveedor"):
        if numero:
            num = numero.strip()
            if num.startswith("0"):
                num = "595" + num[1:]
            num = "".join(ch for ch in num if ch.isdigit())
            url = f"https://wa.me/{num}?text=Hola%20{nombre_prov}"
            webbrowser.open(url)
        else:
            show_snackbar("⚠️ Número no válido para WhatsApp.", "#FFA000")

    def abrir_whatsapp_form(e):
        if telefono.value.strip():
            abrir_whatsapp_numero(telefono.value, nombre.value or "proveedor")
        else:
            show_snackbar("⚠️ Ingresa un número de teléfono válido.", "#FFA000")

    telefono_row = ft.Row(
        [
            telefono,
            ft.IconButton(
                icon=ft.icons.CHAT,
                icon_color="#25D366",
                tooltip="Contactar por WhatsApp",
                on_click=abrir_whatsapp_form,
            ),
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=5,
    )

    # --- Filtros ---
    filtro_nombre = ft.TextField(label="Buscar por Nombre", width=200, prefix_icon=ft.icons.SEARCH, on_change=lambda e: refrescar_tabla())
    filtro_ruc = ft.TextField(label="Buscar por RUC", width=200, prefix_icon=ft.icons.SEARCH, on_change=lambda e: refrescar_tabla())

    # ---------------- FUNCIONES ----------------
    def validar_campos():
        if not nombre.value.strip():
            return "⚠️ El nombre es obligatorio."
        if not telefono.value.strip().isdigit():
            return "⚠️ El teléfono debe contener solo números y no estar vacío."
        if not ruc.value.strip():
            return "⚠️ El RUC es obligatorio."
        if correo.value and "@" not in correo.value:
            return "⚠️ El correo no tiene un formato válido."
        return None

    def limpiar_form():
        nombre.value = ""
        telefono.value = ""
        correo.value = ""
        direccion.value = ""
        ruc.value = ""
        error_msg.value = ""
        selected_id["id"] = None
        proveedor_original["data"] = None
        page.update()

    # ---------------- CRUD ----------------
    def agregar_proveedor(e):
        msg = validar_campos()
        if msg:
            show_snackbar(msg, "#FFA000")
            page.update()
            return

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO proveedores (nombre, telefono, correo, direccion, ruc) VALUES (?,?,?,?,?)",
            (nombre.value, telefono.value, correo.value, direccion.value, ruc.value),
        )
        conn.commit()
        conn.close()
        limpiar_form()
        refrescar_tabla()
        show_snackbar("✅ Proveedor agregado correctamente.", "#2E7D32")

    def refrescar_tabla():
        tabla.rows.clear()
        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        query = "SELECT id, nombre, telefono, correo, direccion, ruc FROM proveedores WHERE 1=1"
        params = []

        if filtro_nombre.value.strip():
            query += " AND nombre LIKE ?"
            params.append(f"%{filtro_nombre.value.strip()}%")

        if filtro_ruc.value.strip():
            query += " AND ruc LIKE ?"
            params.append(f"%{filtro_ruc.value.strip()}%")

        query += " ORDER BY nombre ASC"

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        for prov in rows:
            pid, p_nombre, p_tel, p_correo, p_direccion, p_ruc = prov
            tabla.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(pid), text_align="center")),
                        ft.DataCell(ft.Text(p_nombre or "", text_align="left")),
                        ft.DataCell(ft.Text(p_tel or "", text_align="center")),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.CHAT,
                                icon_color="#25D366",
                                tooltip=f"Contactar a {p_nombre or 'proveedor'}",
                                on_click=lambda e, num=p_tel, nom=p_nombre: abrir_whatsapp_numero(num, nom),
                            )
                        ),
                        ft.DataCell(ft.Text(p_correo or "", text_align="center")),
                        ft.DataCell(ft.Text(p_direccion or "", text_align="left")),
                        ft.DataCell(ft.Text(p_ruc or "", text_align="center")),
                    ],
                    on_select_changed=lambda e, pid=pid: seleccionar(pid),
                )
            )
        page.update()

    def seleccionar(pid):
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM proveedores WHERE id=?", (pid,))
        prov = cur.fetchone()
        conn.close()
        if prov:
            selected_id["id"] = prov[0]
            proveedor_original["data"] = prov
            nombre.value = prov[1]
            telefono.value = prov[2]
            correo.value = prov[3]
            direccion.value = prov[4]
            ruc.value = prov[5]
            error_msg.value = ""
            page.update()

    def editar_proveedor(e):
        if not selected_id["id"]:
            show_snackbar("⚠️ Selecciona un proveedor para editar.", "#FFA000")
            page.update()
            return

        msg = validar_campos()
        if msg:
            show_snackbar(msg, "#FFA000")
            page.update()
            return

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute(
            "UPDATE proveedores SET nombre=?, telefono=?, correo=?, direccion=?, ruc=? WHERE id=?",
            (nombre.value, telefono.value, correo.value, direccion.value, ruc.value, selected_id["id"]),
        )
        conn.commit()
        conn.close()
        limpiar_form()
        refrescar_tabla()
        show_snackbar("✏️ Proveedor editado correctamente.", "#0288D1")

    def eliminar_proveedor(e):
        if not selected_id["id"]:
            show_snackbar("⚠️ Selecciona un proveedor para eliminar.", "#FFA000")
            page.update()
            return
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM proveedores WHERE id=?", (selected_id["id"],))
        conn.commit()
        conn.close()
        limpiar_form()
        refrescar_tabla()
        show_snackbar("🗑️ Proveedor eliminado correctamente.", "#C62828")

    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", text_align="center", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Nombre", text_align="left", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Teléfono", text_align="center", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("WhatsApp", text_align="center", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Correo", text_align="center", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Dirección", text_align="left", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("RUC", text_align="center", color=PRIMARY_COLOR)),
        ],
        rows=[],
        column_spacing=8,
    )

    refrescar_tabla()

    botones = ft.Row(
        [
            ft.ElevatedButton("Agregar", on_click=agregar_proveedor, bgcolor=PRIMARY_COLOR, color="white", icon=ft.icons.ADD),
            ft.ElevatedButton("Editar", on_click=editar_proveedor, bgcolor="#0288D1", color="white", icon=ft.icons.EDIT),
            ft.ElevatedButton("Eliminar", on_click=eliminar_proveedor, bgcolor="#C62828", color="white", icon=ft.icons.DELETE),
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
                ft.Row([volver_icon, ft.Text("Gestión de Proveedores", size=25, weight="bold", color="black")]),
                nombre,
                telefono_row,  # <- Teléfono con botón WhatsApp
                correo,
                direccion,
                ruc,
                error_msg,
                botones,
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        ),
        width=500,
        padding=30,
        border_radius=20,
        bgcolor=ft.colors.with_opacity(0.7, ft.colors.WHITE),
        shadow=ft.BoxShadow(blur_radius=15, color="#444"),
    )

    tabla_card = ft.Container(
        content=ft.Column(
            [
                ft.Row([filtro_nombre, filtro_ruc], spacing=15),
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
        width=800,
    )

    content.controls.append(
        ft.Row(
            [form_card, tabla_card],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            expand=True,
        )
    )
    if page:
        page.update()