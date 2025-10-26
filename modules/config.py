"""
Configuración centralizada del sistema Vivero Rocío
Incluye constantes, estilos y configuraciones globales
"""
import os

# ========================================
# CONFIGURACIÓN DE BASE DE DATOS
# ========================================
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Fallback a SQLite solo para desarrollo local
    DATABASE_URL = "sqlite:///data/vivero.db"
    print("⚠️ Usando SQLite para desarrollo local")

# Pool de conexiones
DB_POOL_MIN = 1
DB_POOL_MAX = 10
DB_TIMEOUT = 10

# ========================================
# CONFIGURACIÓN DE SEGURIDAD
# ========================================
# Bcrypt rounds (10-12 recomendado para producción)
BCRYPT_ROUNDS = 12

# Intentos máximos de login
MAX_LOGIN_ATTEMPTS = 5
LOGIN_TIMEOUT_MINUTES = 15

# ========================================
# CONFIGURACIÓN DE UI/UX
# ========================================

# Paleta de colores principal
class Colors:
    # Colores primarios del vivero
    PRIMARY = "#2E7D32"           # Verde principal
    PRIMARY_LIGHT = "#4CAF50"     # Verde claro
    PRIMARY_DARK = "#1B5E20"      # Verde oscuro

    # Colores de acento
    ACCENT = "#66BB6A"            # Verde acento
    ACCENT_LIGHT = "#81C784"      # Verde acento claro

    # Colores de estado
    SUCCESS = "#4CAF50"           # Éxito
    WARNING = "#FF9800"           # Advertencia
    ERROR = "#F44336"             # Error
    INFO = "#2196F3"              # Información

    # Colores de fondo
    BG_LIGHT = "#F5F5F5"          # Fondo claro
    BG_WHITE = "#FFFFFF"          # Fondo blanco
    BG_DARK = "#1B2430"           # Fondo oscuro
    SIDEBAR_BG = "#1B2430"        # Fondo sidebar
    CARD_BG = "#FFFFFF"           # Fondo tarjetas

    # Colores de texto
    TEXT_PRIMARY = "#212121"      # Texto principal
    TEXT_SECONDARY = "#757575"    # Texto secundario
    TEXT_DISABLED = "#BDBDBD"     # Texto deshabilitado
    TEXT_WHITE = "#FFFFFF"        # Texto blanco

    # Colores de bordes
    BORDER_LIGHT = "#E0E0E0"      # Borde claro
    BORDER_DARK = "#9E9E9E"       # Borde oscuro

    # Gradientes
    GRADIENT_START = "#E8F5E9"    # Inicio gradiente
    GRADIENT_END = "#C8E6C9"      # Fin gradiente


# Tamaños de fuente
class FontSizes:
    TINY = 10
    SMALL = 12
    NORMAL = 14
    MEDIUM = 16
    LARGE = 18
    XLARGE = 24
    XXLARGE = 32
    HUGE = 48


# Espaciado
class Spacing:
    TINY = 4
    SMALL = 8
    NORMAL = 12
    MEDIUM = 16
    LARGE = 20
    XLARGE = 24
    XXLARGE = 32


# Tamaños de componentes
class Sizes:
    # Botones
    BUTTON_HEIGHT = 45
    BUTTON_WIDTH_SMALL = 120
    BUTTON_WIDTH_MEDIUM = 200
    BUTTON_WIDTH_LARGE = 300

    # Inputs
    INPUT_HEIGHT = 50
    INPUT_WIDTH_SMALL = 150
    INPUT_WIDTH_MEDIUM = 250
    INPUT_WIDTH_LARGE = 350
    INPUT_WIDTH_XLARGE = 500

    # Contenedores
    CARD_PADDING = 20
    CARD_RADIUS = 10
    CONTAINER_PADDING = 15

    # Sidebar
    SIDEBAR_WIDTH = 250

    # Tablas
    TABLE_ROW_HEIGHT = 50
    TABLE_HEADER_HEIGHT = 60


# Iconos por módulo
class Icons:
    # Módulos principales
    DASHBOARD = "dashboard"
    PRODUCTOS = "spa"
    CLIENTES = "people"
    PROVEEDORES = "local_shipping"
    PEDIDOS = "receipt"
    VENTAS = "paid"
    REPORTES = "insert_chart"
    USUARIOS = "admin_panel_settings"

    # Acciones
    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
    SAVE = "save"
    CANCEL = "cancel"
    SEARCH = "search"
    FILTER = "filter_list"
    REFRESH = "refresh"
    EXPORT = "file_download"
    PRINT = "print"

    # Estado
    SUCCESS = "check_circle"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"

    # Navegación
    BACK = "arrow_back"
    FORWARD = "arrow_forward"
    HOME = "home"
    LOGOUT = "logout"
    LOGIN = "login"

    # Otros
    WHATSAPP = "chat"
    EMAIL = "email"
    PHONE = "phone"
    LOCATION = "location_on"
    CALENDAR = "calendar_today"
    MONEY = "attach_money"


# ========================================
# CONFIGURACIÓN DE PAGINACIÓN
# ========================================
ITEMS_PER_PAGE = 50
MAX_ITEMS_WITHOUT_PAGINATION = 100


# ========================================
# CONFIGURACIÓN DE REPORTES
# ========================================
REPORTES_DIR = "reportes"
TICKETS_DIR = "tickets"
TEMP_DIR = "temp"

# Formato de fecha
DATE_FORMAT = "%d/%m/%Y"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
DATE_FORMAT_DB = "%Y-%m-%d"
DATETIME_FORMAT_DB = "%Y-%m-%d %H:%M:%S"


# ========================================
# CONFIGURACIÓN DE VALIDACIÓN
# ========================================
class Validation:
    # Longitudes
    MIN_PASSWORD_LENGTH = 6
    MAX_PASSWORD_LENGTH = 100
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 50

    # Patrones regex
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^[0-9\s\-\+\(\)]{7,20}$'
    RUC_PATTERN = r'^\d{6,8}-\d{1}$'

    # Valores numéricos
    MAX_STOCK = 1000000
    MAX_PRECIO = 100000000  # 100 millones de Gs.
    MIN_PRECIO = 0


# ========================================
# ROLES Y PERMISOS
# ========================================
class Roles:
    ADMIN = "Administrador"
    GERENTE = "Gerente"
    VENDEDOR = "Vendedor"
    USUARIO = "Usuario"

    ALL = [ADMIN, GERENTE, VENDEDOR, USUARIO]


class Modules:
    PRODUCTOS = "productos"
    CLIENTES = "clientes"
    PROVEEDORES = "proveedores"
    PEDIDOS = "pedidos"
    VENTAS = "ventas"
    REPORTES = "reportes"
    USUARIOS = "usuarios"

    ALL = [PRODUCTOS, CLIENTES, PROVEEDORES, PEDIDOS, VENTAS, REPORTES, USUARIOS]


class Permissions:
    VER = "ver"
    CREAR = "crear"
    EDITAR = "editar"
    ELIMINAR = "eliminar"

    ALL = [VER, CREAR, EDITAR, ELIMINAR]


# ========================================
# CONFIGURACIÓN DE MONEDA
# ========================================
CURRENCY_SYMBOL = "Gs."
CURRENCY_NAME = "Guaraní"
CURRENCY_CODE = "PYG"


# ========================================
# MENSAJES DEL SISTEMA
# ========================================
class Messages:
    # Éxito
    SUCCESS_CREATE = "✅ Registro creado exitosamente"
    SUCCESS_UPDATE = "✅ Registro actualizado exitosamente"
    SUCCESS_DELETE = "✅ Registro eliminado exitosamente"
    SUCCESS_LOGIN = "✅ Inicio de sesión exitoso"

    # Errores
    ERROR_CREATE = "❌ Error al crear el registro"
    ERROR_UPDATE = "❌ Error al actualizar el registro"
    ERROR_DELETE = "❌ Error al eliminar el registro"
    ERROR_LOGIN = "❌ Usuario o contraseña incorrectos"
    ERROR_PERMISSION = "🚫 No tienes permisos para realizar esta acción"
    ERROR_CONNECTION = "❌ Error de conexión a la base de datos"
    ERROR_VALIDATION = "⚠️ Por favor verifica los datos ingresados"

    # Advertencias
    WARNING_EMPTY_FIELDS = "⚠️ Por favor completa todos los campos requeridos"
    WARNING_INVALID_EMAIL = "⚠️ El formato del email no es válido"
    WARNING_INVALID_PHONE = "⚠️ El formato del teléfono no es válido"
    WARNING_INVALID_RUC = "⚠️ El formato del RUC no es válido"
    WARNING_LOW_STOCK = "⚠️ Stock bajo"

    # Info
    INFO_NO_RESULTS = "ℹ️ No se encontraron resultados"
    INFO_LOADING = "⏳ Cargando..."
    INFO_SEARCHING = "🔍 Buscando..."


# ========================================
# CONFIGURACIÓN DE MÉTODOS DE PAGO
# ========================================
METODOS_PAGO = [
    "Efectivo",
    "Tarjeta de Crédito",
    "Tarjeta de Débito",
    "Transferencia",
    "Cheque",
    "Giros Tigo",
    "Billetera Personal"
]


# ========================================
# CONFIGURACIÓN DE ESTADOS
# ========================================
class Estados:
    # Pedidos
    PEDIDO_PENDIENTE = "Pendiente"
    PEDIDO_EN_PROCESO = "En Proceso"
    PEDIDO_ENTREGADO = "Entregado"
    PEDIDO_CANCELADO = "Cancelado"

    PEDIDOS_ALL = [PEDIDO_PENDIENTE, PEDIDO_EN_PROCESO, PEDIDO_ENTREGADO, PEDIDO_CANCELADO]

    # Ventas
    VENTA_COMPLETADA = "Completada"
    VENTA_CANCELADA = "Cancelada"
    VENTA_PENDIENTE = "Pendiente"

    VENTAS_ALL = [VENTA_COMPLETADA, VENTA_CANCELADA, VENTA_PENDIENTE]

    # Usuarios
    USUARIO_ACTIVO = "Activo"
    USUARIO_INACTIVO = "Inactivo"

    USUARIOS_ALL = [USUARIO_ACTIVO, USUARIO_INACTIVO]

    # Cajas
    CAJA_ABIERTA = "Abierta"
    CAJA_CERRADA = "Cerrada"

    CAJAS_ALL = [CAJA_ABIERTA, CAJA_CERRADA]


# ========================================
# CATEGORÍAS DE PRODUCTOS
# ========================================
CATEGORIAS_PRODUCTOS = [
    "Plantas Ornamentales",
    "Árboles Frutales",
    "Plantas Aromáticas",
    "Plantas Medicinales",
    "Cactus y Suculentas",
    "Flores de Estación",
    "Plantas de Interior",
    "Plantas de Exterior",
    "Semillas",
    "Fertilizantes",
    "Herramientas",
    "Macetas",
    "Tierra y Sustratos",
    "Otros"
]


# ========================================
# UNIDADES DE MEDIDA
# ========================================
UNIDADES_MEDIDA = [
    "Unidad",
    "Kg",
    "Gramo",
    "Litro",
    "Metro",
    "Bolsa",
    "Caja",
    "Paquete",
    "Docena"
]


# ========================================
# CONFIGURACIÓN DE APLICACIÓN
# ========================================
APP_NAME = "Vivero Rocío"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Sistema de Gestión Integral"
APP_PORT = int(os.environ.get("PORT", 8550))
APP_HOST = "0.0.0.0"


# ========================================
# CONFIGURACIÓN DE LOGS
# ========================================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
