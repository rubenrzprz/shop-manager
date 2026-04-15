import pytest

from app.application.dto.products import UNSET
from app.ui.dialogs.product_dialog import ProductDialog


@pytest.mark.parametrize("raw_value", ["NaN", "sNaN", "Infinity", "-Infinity"])
def test_parse_decimal_rejects_non_finite_values(raw_value):
    with pytest.raises(ValueError, match="Base price must be a finite number."):
        ProductDialog._parse_decimal(raw_value)


def test_supplier_input_value_preserves_existing_supplier_when_edit_options_are_unavailable():
    dialog = ProductDialog.__new__(ProductDialog)
    dialog._product_id = 1
    dialog._supplier_combo = DisabledSupplierCombo()

    assert dialog._supplier_input_value() is UNSET


class DisabledSupplierCombo:
    def isEnabled(self) -> bool:
        return False
