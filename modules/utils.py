"""
Utilidades compartidas para todo el sistema
Funciones de formato, validación, conversión, etc.
"""
import re
import webbrowser
from datetime import datetime
from typing import Optional, Union
from modules.config import (
    CURRENCY_SYMBOL,
    DATE_FORMAT,
    DATETIME_FORMAT,
    Validation
)


# ========================================
# FUNCIONES DE FORMATO DE MONEDA
# ========================================

def format_guarani(valor: Union[int, float, str, None]) -> str:
    """
    Formatea un valor numérico a formato Guaraní
    Ej: 150000 -> "150.000 Gs."
    """
    try:
        # Convertir a entero
        if isinstance(valor, str):
            valor = parse_guarani(valor)
        valor = int(round(float(valor or 0)))

        # Formatear con separadores de miles
        formatted = f"{valor:,}".replace(",", ".")
        return f"{formatted} {CURRENCY_SYMBOL}"
    except (ValueError, TypeError):
        return f"0 {CURRENCY_SYMBOL}"


def parse_guarani(valor: Union[str, int, float, None]) -> int:
    """
    Convierte un string en formato Guaraní a entero
    Ej: "150.000 Gs." -> 150000
    """
    if isinstance(valor, (int, float)):
        return int(valor)

    if valor is None:
        return 0

    try:
        # Remover símbolos de moneda y espacios
        s = str(valor).strip()
        s = s.replace(CURRENCY_SYMBOL, "").replace("Gs", "").replace("gs", "")
        # Remover separadores de miles y espacios
        s = s.replace(".", "").replace(",", "").replace(" ", "")
        # Convertir a entero
        return int(s) if s.isdigit() else 0
    except (ValueError, AttributeError):
        return 0


# ========================================
# FUNCIONES DE FORMATO DE FECHA
# ========================================

def format_date(fecha: Union[datetime, str, None], formato: str = DATE_FORMAT) -> str:
    """
    Formatea una fecha al formato especificado
    """
    if fecha is None:
        return ""

    try:
        if isinstance(fecha, str):
            # Intentar parsear diferentes formatos
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"]:
                try:
                    fecha = datetime.strptime(fecha, fmt)
                    break
                except ValueError:
                    continue

        if isinstance(fecha, datetime):
            return fecha.strftime(formato)

        return str(fecha)
    except (ValueError, AttributeError):
        return ""


def parse_date(fecha_str: str, formato: str = DATE_FORMAT) -> Optional[datetime]:
    """
    Convierte un string a datetime
    """
    if not fecha_str:
        return None

    try:
        return datetime.strptime(fecha_str, formato)
    except ValueError:
        return None


def get_current_date_str(formato: str = DATE_FORMAT) -> str:
    """
    Retorna la fecha actual como string
    """
    return datetime.now().strftime(formato)


def get_current_datetime_str(formato: str = DATETIME_FORMAT) -> str:
    """
    Retorna la fecha y hora actual como string
    """
    return datetime.now().strftime(formato)


# ========================================
# FUNCIONES DE VALIDACIÓN
# ========================================

def validate_email(email: str) -> bool:
    """
    Valida formato de email
    """
    if not email:
        return False

    pattern = re.compile(Validation.EMAIL_PATTERN)
    return bool(pattern.match(email.strip()))


def validate_phone(telefono: str) -> bool:
    """
    Valida formato de teléfono
    """
    if not telefono:
        return False

    pattern = re.compile(Validation.PHONE_PATTERN)
    return bool(pattern.match(telefono.strip()))


def validate_ruc(ruc: str) -> bool:
    """
    Valida formato de RUC paraguayo
    Formato: XXXXXX-X o XXXXXXX-X o XXXXXXXX-X
    """
    if not ruc:
        return False

    # Patrón básico
    pattern = re.compile(Validation.RUC_PATTERN)
    if not pattern.match(ruc.strip()):
        return False

    # Validación de dígito verificador (algoritmo módulo 11)
    try:
        ruc_clean = ruc.replace("-", "")
        base = ruc_clean[:-1]
        dv = int(ruc_clean[-1])

        # Calcular dígito verificador
        total = 0
        k = 2
        for digit in reversed(base):
            total += int(digit) * k
            k = k + 1 if k < 9 else 2

        verificador = 11 - (total % 11)
        if verificador == 11:
            verificador = 0
        elif verificador == 10:
            verificador = 1

        return verificador == dv
    except (ValueError, IndexError):
        return False


def sanitize_string(texto: str) -> str:
    """
    Limpia y sanitiza un string
    """
    if not texto:
        return ""

    # Remover espacios extra y caracteres especiales peligrosos
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)  # Múltiples espacios a uno solo
    return texto


def normalize_phone(telefono: str) -> str:
    """
    Normaliza número de teléfono paraguayo
    """
    if not telefono:
        return ""

    # Remover todo excepto dígitos y el símbolo +
    telefono = re.sub(r'[^\d+]', '', telefono)

    # Si empieza con 0, reemplazar con código de país
    if telefono.startswith("0"):
        telefono = "595" + telefono[1:]

    # Si no tiene código de país, agregarlo
    if not telefono.startswith("+") and not telefono.startswith("595"):
        telefono = "595" + telefono

    return telefono


# ========================================
# FUNCIONES DE INTEGRACIÓN WHATSAPP
# ========================================

def open_whatsapp(telefono: str, nombre: str = "cliente", mensaje: str = "") -> bool:
    """
    Abre WhatsApp Web con un número de teléfono
    """
    try:
        # Normalizar teléfono
        phone = normalize_phone(telefono)

        # Remover el símbolo + si existe
        phone = phone.replace("+", "")

        # Mensaje por defecto
        if not mensaje:
            mensaje = f"Hola {nombre}"

        # URL encode del mensaje
        mensaje_encoded = re.sub(r'\s+', '%20', mensaje)

        # Abrir WhatsApp Web
        url = f"https://wa.me/{phone}?text={mensaje_encoded}"
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"Error abriendo WhatsApp: {e}")
        return False


# ========================================
# FUNCIONES DE GENERACIÓN
# ========================================

def generar_numero_venta() -> str:
    """
    Genera un número único de venta
    Formato: VYYYYMMDDHHMMSS
    """
    now = datetime.now()
    return f"V{now.strftime('%Y%m%d%H%M%S')}"


def generar_numero_pedido() -> str:
    """
    Genera un número único de pedido
    Formato: PYYYYMMDDHHMMSS
    """
    now = datetime.now()
    return f"P{now.strftime('%Y%m%d%H%M%S')}"


# ========================================
# FUNCIONES DE BÚSQUEDA Y FILTRADO
# ========================================

def buscar_en_texto(texto: str, busqueda: str) -> bool:
    """
    Busca un término en un texto (case-insensitive)
    """
    if not texto or not busqueda:
        return False

    return busqueda.lower() in texto.lower()


def filtrar_lista_por_texto(lista: list, campo: str, busqueda: str) -> list:
    """
    Filtra una lista de diccionarios por un campo de texto
    """
    if not busqueda:
        return lista

    return [
        item for item in lista
        if buscar_en_texto(str(item.get(campo, "")), busqueda)
    ]


# ========================================
# FUNCIONES DE CÁLCULO
# ========================================

def calcular_subtotal(cantidad: Union[int, float], precio_unitario: Union[int, float]) -> int:
    """
    Calcula el subtotal de un producto
    """
    try:
        cantidad = float(cantidad or 0)
        precio_unitario = float(precio_unitario or 0)
        return int(round(cantidad * precio_unitario))
    except (ValueError, TypeError):
        return 0


def calcular_total_con_descuento(subtotal: Union[int, float], descuento: Union[int, float] = 0) -> int:
    """
    Calcula el total aplicando descuento
    """
    try:
        subtotal = float(subtotal or 0)
        descuento = float(descuento or 0)
        return int(round(subtotal - descuento))
    except (ValueError, TypeError):
        return 0


def calcular_vuelto(total: Union[int, float], monto_pagado: Union[int, float]) -> int:
    """
    Calcula el vuelto
    """
    try:
        total = float(total or 0)
        monto_pagado = float(monto_pagado or 0)
        vuelto = int(round(monto_pagado - total))
        return max(0, vuelto)
    except (ValueError, TypeError):
        return 0


# ========================================
# FUNCIONES DE CONVERSIÓN
# ========================================

def to_int(valor: Union[str, int, float, None], default: int = 0) -> int:
    """
    Convierte un valor a entero de forma segura
    """
    try:
        if valor is None:
            return default
        return int(float(valor))
    except (ValueError, TypeError):
        return default


def to_float(valor: Union[str, int, float, None], default: float = 0.0) -> float:
    """
    Convierte un valor a float de forma segura
    """
    try:
        if valor is None:
            return default
        return float(valor)
    except (ValueError, TypeError):
        return default


def to_bool(valor: Union[str, int, bool, None], default: bool = False) -> bool:
    """
    Convierte un valor a booleano de forma segura
    """
    if valor is None:
        return default

    if isinstance(valor, bool):
        return valor

    if isinstance(valor, (int, float)):
        return valor != 0

    if isinstance(valor, str):
        return valor.lower() in ('true', '1', 'yes', 'si', 's', 'y')

    return default


# ========================================
# FUNCIONES DE STRING
# ========================================

def truncate(texto: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Trunca un texto a una longitud máxima
    """
    if not texto:
        return ""

    if len(texto) <= max_length:
        return texto

    return texto[:max_length - len(suffix)] + suffix


def capitalize_words(texto: str) -> str:
    """
    Capitaliza la primera letra de cada palabra
    """
    if not texto:
        return ""

    return " ".join(word.capitalize() for word in texto.split())


# ========================================
# FUNCIONES DE LISTAS
# ========================================

def chunk_list(lista: list, chunk_size: int) -> list:
    """
    Divide una lista en chunks de tamaño específico
    """
    return [lista[i:i + chunk_size] for i in range(0, len(lista), chunk_size)]


def paginate_list(lista: list, page: int = 1, items_per_page: int = 50) -> tuple:
    """
    Pagina una lista
    Retorna: (items_de_la_pagina, total_items, total_paginas)
    """
    total_items = len(lista)
    total_paginas = (total_items + items_per_page - 1) // items_per_page

    start = (page - 1) * items_per_page
    end = start + items_per_page

    items_pagina = lista[start:end]

    return items_pagina, total_items, total_paginas
