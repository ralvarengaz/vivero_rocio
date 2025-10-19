import flet as ft
import sqlite3
import hashlib
from modules import dashboard
from datetime import datetime

DB = "data/vivero.db"
PRIMARY_COLOR = "#2E7D32"
ACCENT_COLOR = "#66BB6A"

def crud_view(content, page=None):
    content.controls.clear()

    # --- Barra de mensajes
    def show_snackbar(msg, color):
        page.open(ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color, duration=3000))

    # --- Variables de estado ---
    selected_id = {"id": None}
    usuario_actual = "ralvarengazz"  # Usuario logueado (en producción vendría de sesión)

    # --- Campos del formulario ---
    username = ft.TextField(label="Nombre de Usuario", width=200, hint_text="usuario123", prefix_icon=ft.Icons.PERSON)
    password = ft.TextField(label="Contraseña", width=200, password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK)
    nombre_completo = ft.TextField(label="Nombre Completo", width=300, hint_text="Juan Pérez", prefix_icon=ft.Icons.BADGE)
    email = ft.TextField(label="Email", width=250, hint_text="usuario@email.com", prefix_icon=ft.Icons.EMAIL)
    telefono = ft.TextField(label="Teléfono", width=180, hint_text="0981123456", prefix_icon=ft.Icons.PHONE)
    
    rol = ft.Dropdown(
        label="Rol",
        width=150,
        options=[
            ft.dropdown.Option("Administrador"),
            ft.dropdown.Option("Gerente"),
            ft.dropdown.Option("Vendedor"),
            ft.dropdown.Option("Usuario"),
        ],
        value="Usuario"
    )
    
    estado = ft.Dropdown(
        label="Estado",
        width=120,
        options=[
            ft.dropdown.Option("Activo"),
            ft.dropdown.Option("Inactivo"),
        ],
        value="Activo"
    )

    # --- Permisos por módulo ---
    modulos = ['productos', 'clientes', 'proveedores', 'pedidos', 'ventas', 'reportes', 'usuarios']
    permisos_checkboxes = {}
    
    def crear_permisos_ui():
        permisos_column = ft.Column(spacing=10)
        permisos_column.controls.append(ft.Text("Permisos por Módulo:", size=16, weight="bold", color=PRIMARY_COLOR))
        
        for modulo in modulos:
            permisos_checkboxes[modulo] = {
                'ver': ft.Checkbox(label="Ver", value=False),
                'crear': ft.Checkbox(label="Crear", value=False),
                'editar': ft.Checkbox(label="Editar", value=False),
                'eliminar': ft.Checkbox(label="Eliminar", value=False),
            }
            
            modulo_row = ft.Row([
                ft.Container(ft.Text(modulo.capitalize(), weight="bold"), width=100),
                permisos_checkboxes[modulo]['ver'],
                permisos_checkboxes[modulo]['crear'],
                permisos_checkboxes[modulo]['editar'],
                permisos_checkboxes[modulo]['eliminar'],
            ], spacing=10)
            
            permisos_column.controls.append(modulo_row)
        
        return permisos_column

    permisos_ui = crear_permisos_ui()

    # --- Filtros ---
    filtro_username = ft.TextField(label="Buscar por Usuario", width=180, prefix_icon=ft.Icons.SEARCH)
    filtro_rol = ft.Dropdown(
        label="Filtrar por Rol",
        width=150,
        options=[
            ft.dropdown.Option("", "Todos"),
            ft.dropdown.Option("Administrador"),
            ft.dropdown.Option("Gerente"),
            ft.dropdown.Option("Vendedor"),
            ft.dropdown.Option("Usuario"),
        ],
        value=""
    )

    # --- Tabla de usuarios ---
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Usuario", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Nombre Completo", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Email", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Rol", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Estado", color=PRIMARY_COLOR)),
            ft.DataColumn(ft.Text("Último Acceso", color=PRIMARY_COLOR)),
        ],
        rows=[],
        column_spacing=8,
    )

    error_msg = ft.Text("", color="red")

    # --- Funciones auxiliares ---
    def hashear_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def aplicar_permisos_por_rol(rol_seleccionado):
        """Aplica permisos predeterminados según el rol"""
        permisos_por_rol = {
            'Administrador': {'ver': True, 'crear': True, 'editar': True, 'eliminar': True},
            'Gerente': {'ver': True, 'crear': True, 'editar': True, 'eliminar': False},
            'Vendedor': {'ver': True, 'crear': True, 'editar': False, 'eliminar': False},
            'Usuario': {'ver': True, 'crear': False, 'editar': False, 'eliminar': False},
        }
        
        permisos = permisos_por_rol.get(rol_seleccionado, permisos_por_rol['Usuario'])
        
        for modulo in modulos:
            if modulo == 'usuarios' and rol_seleccionado != 'Administrador':
                # Solo administradores pueden gestionar usuarios
                for accion in permisos_checkboxes[modulo]:
                    permisos_checkboxes[modulo][accion].value = False
            else:
                for accion, permitido in permisos.items():
                    permisos_checkboxes[modulo][accion].value = permitido
        
        page.update()

    def limpiar_form():
        username.value = ""
        password.value = ""
        nombre_completo.value = ""
        email.value = ""
        telefono.value = ""
        rol.value = "Usuario"
        estado.value = "Activo"
        selected_id["id"] = None
        error_msg.value = ""
        
        # Limpiar permisos
        for modulo in modulos:
            for accion in permisos_checkboxes[modulo]:
                permisos_checkboxes[modulo][accion].value = False
        
        page.update()

    def validar_campos():
        errores = []
        if not username.value.strip():
            errores.append("El nombre de usuario es obligatorio")
        if not password.value.strip() and not selected_id["id"]:
            errores.append("La contraseña es obligatoria")
        if not nombre_completo.value.strip():
            errores.append("El nombre completo es obligatorio")
        if email.value.strip() and "@" not in email.value:
            errores.append("El email debe tener un formato válido")
        if len(username.value.strip()) < 3:
            errores.append("El nombre de usuario debe tener al menos 3 caracteres")
        if password.value.strip() and len(password.value.strip()) < 4:
            errores.append("La contraseña debe tener al menos 4 caracteres")
        
        return errores

    # --- Funciones CRUD ---
    def refrescar_tabla(e=None):
        tabla.rows.clear()
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        query = """SELECT id, username, nombre_completo, email, rol, estado, ultimo_acceso
                   FROM usuarios WHERE 1=1"""
        params = []
        
        if filtro_username.value.strip():
            query += " AND LOWER(username) LIKE ?"
            params.append(f"%{filtro_username.value.strip().lower()}%")
        
        if filtro_rol.value:
            query += " AND rol = ?"
            params.append(filtro_rol.value)
        
        query += " ORDER BY fecha_creacion DESC"
        
        cur.execute(query, params)
        usuarios = cur.fetchall()
        conn.close()
        
        for usuario in usuarios:
            uid, uname, nombre, email_u, rol_u, estado_u, ultimo_acceso = usuario
            
            # Contenedor de estado con color
            estado_color = "#4CAF50" if estado_u == "Activo" else "#F44336"
            estado_container = ft.Container(
                content=ft.Text(estado_u, color="white", weight="bold", size=12),
                bgcolor=estado_color,
                padding=ft.padding.symmetric(vertical=4, horizontal=8),
                border_radius=8
            )
            
            # Contenedor de rol con color
            rol_colors = {
                "Administrador": "#D32F2F",
                "Gerente": "#1976D2", 
                "Vendedor": "#388E3C",
                "Usuario": "#757575"
            }
            rol_container = ft.Container(
                content=ft.Text(rol_u, color="white", weight="bold", size=12),
                bgcolor=rol_colors.get(rol_u, "#757575"),
                padding=ft.padding.symmetric(vertical=4, horizontal=8),
                border_radius=8
            )
            
            tabla.rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(uid))),
                    ft.DataCell(ft.Text(uname)),
                    ft.DataCell(ft.Text(nombre)),
                    ft.DataCell(ft.Text(email_u or "")),
                    ft.DataCell(rol_container),
                    ft.DataCell(estado_container),
                    ft.DataCell(ft.Text(ultimo_acceso or "Nunca")),
                ],
                on_select_changed=lambda e, uid=uid: seleccionar(uid),
            ))
        page.update()

    def seleccionar(uid):
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        # Obtener datos del usuario
        cur.execute("SELECT * FROM usuarios WHERE id=?", (uid,))
        usuario = cur.fetchone()
        
        if usuario:
            selected_id["id"] = usuario[0]
            username.value = usuario[1]
            password.value = ""  # No mostrar contraseña
            nombre_completo.value = usuario[3]
            email.value = usuario[4] or ""
            telefono.value = usuario[5] or ""
            rol.value = usuario[6]
            estado.value = usuario[7]
            
            # Cargar permisos
            cur.execute("SELECT modulo, puede_ver, puede_crear, puede_editar, puede_eliminar FROM permisos_usuario WHERE usuario_id=?", (uid,))
            permisos = cur.fetchall()
            
            # Limpiar permisos primero
            for modulo in modulos:
                for accion in permisos_checkboxes[modulo]:
                    permisos_checkboxes[modulo][accion].value = False
            
            # Aplicar permisos guardados
            for permiso in permisos:
                modulo, ver, crear, editar, eliminar = permiso
                if modulo in permisos_checkboxes:
                    permisos_checkboxes[modulo]['ver'].value = bool(ver)
                    permisos_checkboxes[modulo]['crear'].value = bool(crear)
                    permisos_checkboxes[modulo]['editar'].value = bool(editar)
                    permisos_checkboxes[modulo]['eliminar'].value = bool(eliminar)
            
            error_msg.value = ""
        
        conn.close()
        page.update()

    def agregar_usuario(e):
        errores = validar_campos()
        if errores:
            error_msg.value = "Errores: " + "; ".join(errores)
            page.update()
            return
        
        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            
            # Verificar si el username ya existe
            cur.execute("SELECT id FROM usuarios WHERE username=?", (username.value.strip(),))
            if cur.fetchone():
                show_snackbar("El nombre de usuario ya existe", "#FFA000")
                conn.close()
                return
            
            # Insertar usuario
            password_hash = hashear_password(password.value.strip())
            cur.execute("""
                INSERT INTO usuarios (username, password, nombre_completo, email, telefono, rol, estado, creado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?, (SELECT id FROM usuarios WHERE username=? LIMIT 1))
            """, (username.value.strip(), password_hash, nombre_completo.value.strip(), 
                  email.value.strip() or None, telefono.value.strip() or None, 
                  rol.value, estado.value, usuario_actual))
            
            usuario_id = cur.lastrowid
            
            # Insertar permisos
            for modulo in modulos:
                permisos = permisos_checkboxes[modulo]
                cur.execute("""
                    INSERT INTO permisos_usuario (usuario_id, modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (usuario_id, modulo, 
                      permisos['ver'].value, permisos['crear'].value, 
                      permisos['editar'].value, permisos['eliminar'].value))
            
            conn.commit()
            conn.close()
            
            limpiar_form()
            refrescar_tabla()
            show_snackbar("Usuario creado correctamente", PRIMARY_COLOR)
            
        except Exception as ex:
            show_snackbar(f"Error al crear usuario: {str(ex)}", "#F44336")

    def editar_usuario(e):
        if not selected_id["id"]:
            show_snackbar("Selecciona un usuario para editar", "#FFA000")
            return
        
        errores = validar_campos()
        # Quitar validación de contraseña para edición
        errores = [e for e in errores if "contraseña" not in e.lower()]
        if errores:
            error_msg.value = "Errores: " + "; ".join(errores)
            page.update()
            return
        
        try:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            
            # Verificar username único (excluyendo el usuario actual)
            cur.execute("SELECT id FROM usuarios WHERE username=? AND id!=?", (username.value.strip(), selected_id["id"]))
            if cur.fetchone():
                show_snackbar("El nombre de usuario ya existe", "#FFA000")
                conn.close()
                return
            
            # Actualizar usuario
            if password.value.strip():
                password_hash = hashear_password(password.value.strip())
                cur.execute("""
                    UPDATE usuarios SET username=?, password=?, nombre_completo=?, email=?, telefono=?, rol=?, estado=?
                    WHERE id=?
                """, (username.value.strip(), password_hash, nombre_completo.value.strip(),
                      email.value.strip() or None, telefono.value.strip() or None,
                      rol.value, estado.value, selected_id["id"]))
            else:
                cur.execute("""
                    UPDATE usuarios SET username=?, nombre_completo=?, email=?, telefono=?, rol=?, estado=?
                    WHERE id=?
                """, (username.value.strip(), nombre_completo.value.strip(),
                      email.value.strip() or None, telefono.value.strip() or None,
                      rol.value, estado.value, selected_id["id"]))
            
            # Actualizar permisos
            cur.execute("DELETE FROM permisos_usuario WHERE usuario_id=?", (selected_id["id"],))
            for modulo in modulos:
                permisos = permisos_checkboxes[modulo]
                cur.execute("""
                    INSERT INTO permisos_usuario (usuario_id, modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (selected_id["id"], modulo,
                      permisos['ver'].value, permisos['crear'].value,
                      permisos['editar'].value, permisos['eliminar'].value))
            
            conn.commit()
            conn.close()
            
            limpiar_form()
            refrescar_tabla()
            show_snackbar("Usuario editado correctamente", "#0288D1")
            
        except Exception as ex:
            show_snackbar(f"Error al editar usuario: {str(ex)}", "#F44336")

    def eliminar_usuario(e):
        if not selected_id["id"]:
            show_snackbar("Selecciona un usuario para eliminar", "#FFA000")
            return
        
        if selected_id["id"] == 1:  # Proteger admin principal
            show_snackbar("No se puede eliminar el usuario administrador principal", "#FFA000")
            return
        
        def confirmar_eliminacion(respuesta):
            if respuesta:
                try:
                    conn = sqlite3.connect(DB)
                    cur = conn.cursor()
                    
                    # Eliminar permisos primero
                    cur.execute("DELETE FROM permisos_usuario WHERE usuario_id=?", (selected_id["id"],))
                    # Eliminar usuario
                    cur.execute("DELETE FROM usuarios WHERE id=?", (selected_id["id"],))
                    
                    conn.commit()
                    conn.close()
                    
                    limpiar_form()
                    refrescar_tabla()
                    show_snackbar("Usuario eliminado correctamente", "#C62828")
                    
                except Exception as ex:
                    show_snackbar(f"Error al eliminar usuario: {str(ex)}", "#F44336")
            
            page.dialog = None
            page.update()
        
        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Eliminar usuario?"),
            content=ft.Text("¿Estás seguro de que deseas eliminar este usuario y todos sus permisos? Esta acción no puede deshacerse."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: confirmar_eliminacion(False)),
                ft.TextButton("Eliminar", on_click=lambda e: confirmar_eliminacion(True)),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        page.dialog.open = True
        page.update()

    # --- UI Layout ---
    
    # Botones de acción
    botones = ft.Row([
        ft.ElevatedButton("Crear Usuario", on_click=agregar_usuario, bgcolor=PRIMARY_COLOR, color="white", icon=ft.Icons.ADD),
        ft.ElevatedButton("Editar Usuario", on_click=editar_usuario, bgcolor="#0288D1", color="white", icon=ft.Icons.EDIT),
        ft.ElevatedButton("Eliminar Usuario", on_click=eliminar_usuario, bgcolor="#C62828", color="white", icon=ft.Icons.DELETE),
        ft.ElevatedButton("Limpiar", on_click=lambda e: limpiar_form(), bgcolor="#757575", color="white", icon=ft.Icons.CLEAR),
    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=10)

    # Botón para aplicar permisos por rol
    btn_aplicar_rol = ft.ElevatedButton(
        "Aplicar Permisos por Rol",
        bgcolor="#FF9800",
        color="white",
        icon=ft.Icons.SECURITY,
        on_click=lambda e: aplicar_permisos_por_rol(rol.value)
    )

    volver_icon = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        tooltip="Volver al Dashboard",
        icon_color=PRIMARY_COLOR,
        on_click=lambda e: dashboard.dashboard_view(content, page=page),
    )

    # Formulario principal
    form_card = ft.Container(
        content=ft.Column([
            ft.Row([volver_icon, ft.Text("Gestión de Usuarios", size=25, weight="bold", color="black")]),
            ft.Row([username, password], spacing=15),
            ft.Row([nombre_completo], spacing=15),
            ft.Row([email, telefono], spacing=15),
            ft.Row([rol, estado, btn_aplicar_rol], spacing=15),
            ft.Divider(),
            permisos_ui,
            error_msg,
            botones,
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.START, scroll=ft.ScrollMode.AUTO),
        width=700,
        height=600,
        padding=30,
        border_radius=20,
        bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        shadow=ft.BoxShadow(blur_radius=15, color="#444"),
    )

    # Filtros y tabla
    filtros_card = ft.Container(
        content=ft.Row([filtro_username, filtro_rol], spacing=15),
        padding=10,
        border_radius=10,
        bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
    )

    tabla_card = ft.Container(
        content=ft.Column([
            filtros_card,
            ft.ListView(
                controls=[ft.Row([tabla], expand=True, scroll=ft.ScrollMode.AUTO)],
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
        shadow=ft.BoxShadow(blur_radius=15, color="#444"),
        width=650,
    )

    content.controls.append(
        ft.Row([form_card, tabla_card], alignment=ft.MainAxisAlignment.SPACE_EVENLY, expand=True)
    )

    # --- Eventos ---
    filtro_username.on_change = refrescar_tabla
    filtro_rol.on_change = refrescar_tabla

    # --- Cargar datos iniciales ---
    refrescar_tabla()

    if page:
        page.update()