import pytest

from app.application.dto.suppliers import SupplierPickerItem
from app.ui.dialogs.product_dialog import ProductDialog
from app.ui.dialogs.supplier_picker_dialog import SupplierPickerDialog


@pytest.mark.parametrize("raw_value", ["NaN", "sNaN", "Infinity", "-Infinity"])
def test_parse_decimal_rejects_non_finite_values(raw_value):
    with pytest.raises(ValueError, match="Base price must be a finite number."):
        ProductDialog._parse_decimal(raw_value)


def test_supplier_input_value_returns_selected_supplier_id():
    dialog = ProductDialog.__new__(ProductDialog)
    dialog._selected_supplier_id = 12

    assert dialog._supplier_input_value() == 12


def test_supplier_picker_matches_name_tax_id_phone_and_email():
    supplier = SupplierPickerItem(
        id=1,
        name="Tejidos Atlántico",
        tax_id="B12345678",
        phone="+34 600000000",
        email="supplier@example.com",
        is_active=True,
    )

    assert SupplierPickerDialog._matches_supplier(supplier, "tejidos")
    assert SupplierPickerDialog._matches_supplier(supplier, "b123")
    assert SupplierPickerDialog._matches_supplier(supplier, "600000000")
    assert SupplierPickerDialog._matches_supplier(supplier, "example.com")
    assert not SupplierPickerDialog._matches_supplier(supplier, "la orotava")
