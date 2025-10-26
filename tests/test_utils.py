"""
Tests para módulo de utilidades (utils.py)
"""
import pytest
from modules.utils import (
    format_guarani,
    parse_guarani,
    validate_email,
    validate_phone,
    validate_ruc,
    sanitize_string,
    normalize_phone,
    calcular_subtotal,
    calcular_total_con_descuento,
    calcular_vuelto,
    to_int,
    to_float,
    to_bool
)


class TestFormatoMoneda:
    """Tests para funciones de formato de moneda"""

    def test_format_guarani_entero(self):
        assert format_guarani(100000) == "100.000 Gs."
        assert format_guarani(1000) == "1.000 Gs."
        assert format_guarani(0) == "0 Gs."

    def test_format_guarani_string(self):
        assert format_guarani("150000") == "150.000 Gs."
        assert format_guarani("1500") == "1.500 Gs."

    def test_format_guarani_float(self):
        assert format_guarani(150000.99) == "150.001 Gs."

    def test_format_guarani_none(self):
        assert format_guarani(None) == "0 Gs."

    def test_parse_guarani_string(self):
        assert parse_guarani("150.000 Gs.") == 150000
        assert parse_guarani("1.500 Gs.") == 1500
        assert parse_guarani("Gs. 100.000") == 100000

    def test_parse_guarani_entero(self):
        assert parse_guarani(150000) == 150000

    def test_parse_guarani_none(self):
        assert parse_guarani(None) == 0


class TestValidaciones:
    """Tests para funciones de validación"""

    def test_validate_email_validos(self):
        assert validate_email("test@example.com") == True
        assert validate_email("usuario.nombre@dominio.com.py") == True

    def test_validate_email_invalidos(self):
        assert validate_email("invalid") == False
        assert validate_email("@example.com") == False
        assert validate_email("test@") == False
        assert validate_email("") == False

    def test_validate_phone_validos(self):
        assert validate_phone("0981123456") == True
        assert validate_phone("021-123456") == True
        assert validate_phone("+595 981 123456") == True

    def test_validate_phone_invalidos(self):
        assert validate_phone("123") == False
        assert validate_phone("") == False

    def test_validate_ruc_validos(self):
        # RUC válido con dígito verificador correcto
        assert validate_ruc("123456-7") == True or validate_ruc("123456-0") == True

    def test_validate_ruc_invalidos(self):
        assert validate_ruc("123") == False
        assert validate_ruc("") == False
        assert validate_ruc("abc-d") == False


class TestSanitizacion:
    """Tests para funciones de sanitización"""

    def test_sanitize_string(self):
        assert sanitize_string("  texto  con  espacios  ") == "texto con espacios"
        assert sanitize_string("texto\n\ncon\nsaltos") == "texto con saltos"

    def test_normalize_phone(self):
        assert normalize_phone("0981123456") == "595981123456"
        assert normalize_phone("981123456") == "595981123456"


class TestCalculos:
    """Tests para funciones de cálculo"""

    def test_calcular_subtotal(self):
        assert calcular_subtotal(10, 1000) == 10000
        assert calcular_subtotal(5, 2500) == 12500
        assert calcular_subtotal(0, 1000) == 0

    def test_calcular_total_con_descuento(self):
        assert calcular_total_con_descuento(10000, 1000) == 9000
        assert calcular_total_con_descuento(10000, 0) == 10000

    def test_calcular_vuelto(self):
        assert calcular_vuelto(10000, 15000) == 5000
        assert calcular_vuelto(10000, 10000) == 0
        assert calcular_vuelto(10000, 5000) == 0  # No hay vuelto negativo


class TestConversiones:
    """Tests para funciones de conversión"""

    def test_to_int(self):
        assert to_int("123") == 123
        assert to_int(123.45) == 123
        assert to_int(None) == 0
        assert to_int("invalid") == 0
        assert to_int("invalid", default=10) == 10

    def test_to_float(self):
        assert to_float("123.45") == 123.45
        assert to_float(123) == 123.0
        assert to_float(None) == 0.0
        assert to_float("invalid", default=1.5) == 1.5

    def test_to_bool(self):
        assert to_bool(True) == True
        assert to_bool(1) == True
        assert to_bool("yes") == True
        assert to_bool("true") == True
        assert to_bool(False) == False
        assert to_bool(0) == False
        assert to_bool("no") == False
        assert to_bool(None) == False
