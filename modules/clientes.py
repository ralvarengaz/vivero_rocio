import flet as ft
import sqlite3
import webbrowser
from modules import dashboard
from modules.ciudades_paraguay import CIUDADES_PARAGUAY

DB = "data/vivero.db"
PRIMARY_COLOR = "#2E7D32"
ACCENT_COLOR = "#66BB6A"

def crud_view(content, page=None):
    content.controls.clear()

    # --- Campos del formulario ---
    nombre = ft.TextField(label="Nombre", width=300, hint_text="Ej: Juan Pérez", prefix_icon=ft.icons.PERSON)
    ruc = ft.TextField(label="RUC", width=300, hint_text="Ej: 1234567-8", prefix_icon=ft.icons.BADGE)
    ciudad = ft.TextField(label="Ciudad", width=300, hint_text="Buscar ciudad...", prefix_icon=ft.icons.LOCATION_CITY)
    sugerencias_ciudad = ft.Column(visible=False, spacing=5)
    ubicacion = ft.TextField(label="Ubicación", width=300, hint_text="Dirección o coordenadas", prefix_icon=ft.icons.MAP)
    telefono = ft.TextField(label="Teléfono", width=220, hint_text="Ej: 0981123456", prefix_icon=ft.icons.PHONE)
    correo = ft.TextField(label="Correo electrónico", width=300, hint_text="Ej: usuario@email.com", prefix_icon=ft.icons.EMAIL)

    selected_id = {"id": None}
    error_msg = ft.Text("", color="red")

    # --- Función WhatsApp ---
    def abrir_whatsapp_numero(numero, nombre_cli="cliente"):
        if numero:
            num = numero.strip()
            if num.startswith("0"):
                num = "595" + num[1:]
            num = "".join(ch for ch in num if ch.isdigit())
            url = f"https://wa.me/{num}?text=Hola%20{nombre_cli}"
            webbrowser.open(url)
        else:
            show_snackbar("⚠️ Número no válido para WhatsApp.", "#FFA000")

    def abrir_whatsapp_form(e):
        if telefono.value.strip():
            abrir_whatsapp_numero(telefono.value, nombre.value or "cliente")
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

    filtro_nombre = ft.TextField(label="Buscar por Nombre", width=250, prefix_icon=ft.icons.SEARCH)
    filtro_ruc = ft.TextField(label="Buscar por RUC", width=250, prefix_icon=ft.icons.SEARCH)

    def show_snackbar(msg, color):
        page.open(ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color, duration=3000))

    def limpiar_form():
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
        sugerencias_ciudad.controls.clear()
        texto = ciudad.value.strip().lower()
        if texto:
            resultados = [c for c in CIUDADES_PARAGUAY if texto in c.lower()][:5]
            for r in resultados:
                sugerencias_ciudad.controls.append(
                    ft.TextButton(r, on_click=lambda ev, val=r: seleccionar_ciudad(val))
                )
            sugerencias_ciudad.visible = True if resultados else False
        else:
            sugerencias_ciudad.visible = False
        page.update()

    def seleccionar_ciudad(val):
        ciudad.value = val
        sugerencias_ciudad.visible = False
        page.update()

    def refrescar_tabla(e=None):
        tabla.rows.clear()
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        query = "SELECT id, nombre, ruc, telefono, ciudad, ubicacion, correo FROM clientes WHERE 1=1"
        params = []
        if filtro_nombre.value.strip():
            query += " AND nombre LIKE ?"
            params.append(f"%{filtro_nombre.value.strip()}%")
        if filtro_ruc.value.strip():
            query += " AND ruc LIKE ?"
            params.append(f"%{filtro_ruc.value.strip()}%")
        query += " ORDER BY id ASC"
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        for cli in rows:
            cid, c_nombre, c_ruc, c_tel, c_ciudad, c_ubicacion, c_correo = cli
            tabla.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(c_nombre or "")),
                        ft.DataCell(ft.Text(c_ruc or "")),
                        ft.DataCell(ft.Text(c_tel or "")),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.CHAT,
                                icon_color="#25D366",
                                tooltip=f"Contactar a {c_nombre or 'cliente'}",
                                on_click=lambda e, num=c_tel, nom=c_nombre: abrir_whatsapp_numero(num, nom),
                            )
                        ),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.MAP,
                                icon_color=PRIMARY_COLOR,
                                tooltip="Ver ubicación",
                                on_click=lambda e, destino=c_ubicacion: (
                                    webbrowser.open(
                                        f"https://www.google.com/maps/search/?api=1&query={destino}"
                                    ) if destino else None
                                ),
                            )
                        ),
                    ],
                    on_select_changed=lambda e, cid=cid: seleccionar(cid),
                )
            )
        page.update()

    def seleccionar(cid):
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM clientes WHERE id=?", (cid,))
        cli = cur.fetchone()
        conn.close()
        if cli:
            selected_id["id"] = cli[0]     # id
            nombre.value = cli[1]          # nombre
            ruc.value = cli[2]             # ruc
            telefono.value = cli[3]        # telefono
            ciudad.value = cli[4]          # ciudad
            ubicacion.value = cli[5]       # ubicacion
            correo.value = cli[6]          # correo
            error_msg.value = ""
            page.update()

    def agregar_cliente(e):
        errores = []
        if not nombre.value.strip():
            errores.append("El campo Nombre es obligatorio.")
        if not ruc.value.strip():
            errores.append("El campo RUC es obligatorio.")
        if correo.value.strip() and "@" not in correo.value:
            errores.append("El correo debe tener el formato usuario@dominio.com")
        if telefono.value.strip() and not telefono.value.strip().isdigit():
            errores.append("El teléfono debe ser solo números.")
        if errores:
            error_msg.value = "⚠️ " + " ".join(errores)
            page.update()
            return
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT id FROM clientes WHERE ruc=?", (ruc.value.strip(),))
        if cur.fetchone():
            error_msg.value = f"⚠️ Ya existe un cliente con el RUC {ruc.value.strip()}."
            conn.close()
            page.update()
            return
        cur.execute(
            "INSERT INTO clientes (nombre, ruc, telefono, ciudad, ubicacion, correo) VALUES (?,?,?,?,?,?)",
            (nombre.value.strip(), ruc.value.strip(), telefono.value, ciudad.value, ubicacion.value, correo.value),
        )
        conn.commit()
        conn.close()
        limpiar_form()
        refrescar_tabla()
        show_snackbar("✅ Cliente agregado correctamente.", "#2E7D32")

    def editar_cliente(e):
        errores = []
        if not selected_id["id"]:
            errores.append("Selecciona un cliente para editar.")
        if not nombre.value.strip():
            errores.append("El campo Nombre es obligatorio.")
        if not ruc.value.strip():
            errores.append("El campo RUC es obligatorio.")
        if correo.value.strip() and "@" not in correo.value:
            errores.append("El correo debe tener el formato usuario@dominio.com")
        if telefono.value.strip() and not telefono.value.strip().isdigit():
            errores.append("El teléfono debe ser solo números.")
        if errores:
            error_msg.value = "⚠️ " + " ".join(errores)
            page.update()
            return
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT id FROM clientes WHERE ruc=? AND id<>?", (ruc.value.strip(), selected_id["id"]))
        if cur.fetchone():
            error_msg.value = f"⚠️ Ya existe un cliente con el RUC {ruc.value.strip()}."
            conn.close()
            page.update()
            return
        cur.execute(
            "UPDATE clientes SET nombre=?, ruc=?, telefono=?, ciudad=?, ubicacion=?, correo=? WHERE id=?",
            (nombre.value.strip(), ruc.value.strip(), telefono.value, ciudad.value, ubicacion.value, correo.value, selected_id["id"]),
        )
        conn.commit()
        conn.close()
        limpiar_form()
        refrescar_tabla()
        show_snackbar("✏️ Cliente editado correctamente.", "#0288D1")

    def eliminar_cliente(e):
        if not selected_id["id"]:
            error_msg.value = "⚠️ Selecciona un cliente para eliminar."
            page.update()
            return
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM clientes WHERE id=?", (selected_id["id"],))
        conn.commit()
        conn.close()
        limpiar_form()
        refrescar_tabla()
        show_snackbar("🗑️ Cliente eliminado correctamente.", "#C62828")

    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Nombre", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("RUC", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Teléfono", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("WhatsApp", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Ubicación", color=PRIMARY_COLOR)),
        ],
        rows=[],
        column_spacing=8,
    )

    refrescar_tabla()

    botones = ft.Row(
        [
            ft.ElevatedButton("Agregar", on_click=agregar_cliente, bgcolor=PRIMARY_COLOR, color="white", icon=ft.icons.ADD),
            ft.ElevatedButton("Editar", on_click=editar_cliente, bgcolor="#0288D1", color="white", icon=ft.icons.EDIT),
            ft.ElevatedButton("Eliminar", on_click=eliminar_cliente, bgcolor="#C62828", color="white", icon=ft.icons.DELETE),
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
                ft.Row([volver_icon, ft.Text("Gestión de Clientes", size=25, weight="bold")]),
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
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        ),
        width=500,
        padding=25,
        border_radius=20,
        bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        shadow=ft.BoxShadow(blur_radius=12, color="#444"),
    )

    filtros_card = ft.Container(
        content=ft.Row([filtro_nombre, filtro_ruc], spacing=10),
        padding=10,
        border_radius=10,
        bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
    )

    tabla_card = ft.Container(
        content=ft.Column([
            filtros_card,
            ft.ListView(
                controls=[
                    ft.Row(
                        [tabla],
                        expand=True,
                        scroll=ft.ScrollMode.AUTO
                    )
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
        width=650,
    )

    content.controls.append(ft.Row([form_card, tabla_card], alignment=ft.MainAxisAlignment.SPACE_EVENLY, expand=True))

    ciudad.on_change = buscar_ciudad
    filtro_nombre.on_change = refrescar_tabla
    filtro_ruc.on_change = refrescar_tabla

    if page:
        page.update()