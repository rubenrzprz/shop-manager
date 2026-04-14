import pytest

from app.ui.dialogs.product_dialog import ProductDialog


@pytest.mark.parametrize("raw_value", ["NaN", "sNaN", "Infinity", "-Infinity"])
def test_parse_decimal_rejects_non_finite_values(raw_value):
    with pytest.raises(ValueError, match="Base price must be a finite number."):
        ProductDialog._parse_decimal(raw_value)
