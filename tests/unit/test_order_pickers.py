from decimal import Decimal

from app.application.dto.customers import CustomerPickerItem
from app.application.dto.products import ProductVariantPickerItem
from app.domain.enums import CustomerType, DiscountType
from app.ui.dialogs.order_dialog import OrderDialog, _OrderLineItem
from app.ui.dialogs.customer_picker_dialog import CustomerPickerDialog
from app.ui.dialogs.product_variant_picker_dialog import ProductVariantPickerDialog
from app.ui.widgets.products_page import ProductsPage


def test_customer_picker_filter_matches_name_company_tax_phone_and_email():
    customer = CustomerPickerItem(
        id=1,
        customer_type=CustomerType.COMPANY,
        name="Eventos Atlántico",
        company_name="Eventos Atlántico SL",
        tax_id="B12345678",
        phone="+34 600000001",
        email="events@example.com",
        is_active=True,
    )

    assert CustomerPickerDialog._matches_customer(customer, "eventos")
    assert CustomerPickerDialog._matches_customer(customer, "atlántico sl")
    assert CustomerPickerDialog._matches_customer(customer, "b123")
    assert CustomerPickerDialog._matches_customer(customer, "600000001")
    assert CustomerPickerDialog._matches_customer(customer, "events@example")
    assert not CustomerPickerDialog._matches_customer(customer, "la laguna")


def test_product_variant_picker_filter_matches_product_sku_variant_size_and_color():
    variant = ProductVariantPickerItem(
        id=1,
        product_id=2,
        product_name="Traditional Shirt",
        sku="SHIRT-001",
        size="M",
        color="White",
        variant_name="Size M / White",
        price=Decimal("49.90"),
        product_is_active=True,
        variant_is_active=True,
        category_names=["Shirts", "Ceremony"],
    )

    assert ProductVariantPickerDialog._matches_variant(variant, "traditional")
    assert ProductVariantPickerDialog._matches_variant(variant, "shirt-001")
    assert ProductVariantPickerDialog._matches_variant(variant, "size m")
    assert ProductVariantPickerDialog._matches_variant(variant, "m")
    assert ProductVariantPickerDialog._matches_variant(variant, "white")
    assert ProductVariantPickerDialog._matches_variant(variant, "ceremony")
    assert not ProductVariantPickerDialog._matches_variant(variant, "supplier")


def test_product_variant_picker_category_summary_keeps_table_compact():
    assert ProductVariantPickerDialog._category_summary([]) == ""
    assert ProductVariantPickerDialog._category_summary(["Shirts"]) == "Shirts"
    assert ProductVariantPickerDialog._category_summary(["Shirts", "Ceremony", "Sale"]) == (
        "Shirts +2"
    )


def test_products_page_category_summary_keeps_table_compact():
    assert ProductsPage._category_summary([]) == ""
    assert ProductsPage._category_summary(["Category C"]) == "Category C"
    assert ProductsPage._category_summary(["Category C", "Category A", "Sale"]) == "Category C +2"


def test_order_dialog_unit_price_value_distinguishes_unset_from_explicit_zero():
    class FakeUnitPriceInput:
        def __init__(self, value: float) -> None:
            self._value = value

        def value(self) -> float:
            return self._value

    assert OrderDialog._unit_price_value_from_input(FakeUnitPriceInput(-0.01)) is None

    assert OrderDialog._unit_price_value_from_input(FakeUnitPriceInput(0)) == Decimal("0")


def test_order_dialog_quantity_limit_tracks_unit_price_without_underpricing():
    assert OrderDialog._quantity_max_for_unit_price(None) == 999999
    assert OrderDialog._quantity_max_for_unit_price(Decimal("0")) == 999999
    assert OrderDialog._quantity_max_for_unit_price(Decimal("99999999.99")) == 1
    assert OrderDialog._quantity_max_for_unit_price(Decimal("50000000.00")) == 1
    assert OrderDialog._quantity_max_for_unit_price(Decimal("9999.99")) == 10000


def test_order_dialog_builds_all_line_inputs_in_order():
    dialog = OrderDialog.__new__(OrderDialog)
    dialog._line_items = [
        _OrderLineItem(
            order_line_id=None,
            product_variant_id=11,
            product_name="Traditional Shirt",
            sku="SHIRT-001",
            quantity=1,
            unit_price=Decimal("10.00"),
            notes=None,
        ),
        _OrderLineItem(
            order_line_id=None,
            product_variant_id=22,
            product_name="Belt",
            sku="BELT-001",
            quantity=2,
            unit_price=Decimal("15.00"),
            notes="Gift wrap",
        ),
    ]

    lines = dialog._build_line_inputs()

    assert [line.product_variant_id for line in lines] == [11, 22]
    assert [line.quantity for line in lines] == [1, 2]
    assert [line.unit_price for line in lines] == [Decimal("10.00"), Decimal("15.00")]
    assert [line.notes for line in lines] == [None, "Gift wrap"]


def test_order_dialog_rejects_building_order_without_added_lines():
    dialog = OrderDialog.__new__(OrderDialog)
    dialog._line_items = []

    try:
        dialog._build_line_inputs()
    except ValueError as exc:
        assert str(exc) == "Add at least one order line."
    else:
        raise AssertionError("Expected missing lines to be rejected.")


def test_order_dialog_line_subtotal_sums_all_line_items():
    dialog = OrderDialog.__new__(OrderDialog)
    dialog._line_items = [
        _OrderLineItem(
            order_line_id=None,
            product_variant_id=11,
            product_name="Traditional Shirt",
            sku="SHIRT-001",
            quantity=2,
            unit_price=Decimal("10.00"),
            notes=None,
        ),
        _OrderLineItem(
            order_line_id=None,
            product_variant_id=22,
            product_name="Belt",
            sku="BELT-001",
            quantity=1,
            unit_price=Decimal("15.50"),
            notes=None,
        ),
        _OrderLineItem(
            order_line_id=None,
            product_variant_id=33,
            product_name="Complimentary Service",
            sku="SERVICE-001",
            quantity=1,
            unit_price=Decimal("0.00"),
            notes=None,
        ),
    ]

    assert dialog._line_subtotal() == Decimal("35.50")


def test_order_dialog_total_preview_calculates_fixed_discount():
    preview = OrderDialog._calculate_total_preview(
        subtotal=Decimal("35.50"),
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("5.25"),
    )

    assert preview.subtotal == Decimal("35.50")
    assert preview.discount_amount == Decimal("5.25")
    assert preview.total == Decimal("30.25")


def test_order_dialog_total_preview_caps_fixed_discount_at_subtotal():
    preview = OrderDialog._calculate_total_preview(
        subtotal=Decimal("35.50"),
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("99.00"),
    )

    assert preview.subtotal == Decimal("35.50")
    assert preview.discount_amount == Decimal("35.50")
    assert preview.total == Decimal("0.00")


def test_order_dialog_total_preview_calculates_percentage_discount_with_money_rounding():
    preview = OrderDialog._calculate_total_preview(
        subtotal=Decimal("99.99"),
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("12.345"),
    )

    assert preview.subtotal == Decimal("99.99")
    assert preview.discount_amount == Decimal("12.35")
    assert preview.total == Decimal("87.64")


def test_order_dialog_fixed_discount_maximum_uses_loaded_line_subtotal():
    dialog = OrderDialog.__new__(OrderDialog)
    dialog._line_items = [
        _OrderLineItem(
            order_line_id=7,
            product_variant_id=11,
            product_name="Traditional Shirt",
            sku="SHIRT-001",
            quantity=2,
            unit_price=Decimal("10.00"),
            notes="Existing note",
        )
    ]

    class FakeDiscountTypeInput:
        def currentData(self):
            return DiscountType.FIXED

    class FakeDiscountValueInput:
        def __init__(self) -> None:
            self.maximum = None
            self.value_value = 0
            self.enabled = False

        def setEnabled(self, value: bool) -> None:
            self.enabled = value

        def setMaximum(self, value: float) -> None:
            self.maximum = value

        def setValue(self, value: float) -> None:
            self.value_value = min(value, self.maximum)

        def value(self) -> float:
            return self.value_value

    class FakeLabel:
        def setText(self, _value: str) -> None:
            pass

    dialog._discount_type_input = FakeDiscountTypeInput()
    dialog._discount_value_input = FakeDiscountValueInput()
    dialog._subtotal_value_label = FakeLabel()
    dialog._discount_amount_value_label = FakeLabel()
    dialog._total_value_label = FakeLabel()

    dialog._sync_discount_input_state()
    dialog._discount_value_input.setValue(5.0)

    assert dialog._discount_value_input.maximum == 20.0
    assert dialog._discount_value_input.value() == 5.0


def test_order_dialog_builds_update_line_inputs_with_existing_ids_and_notes():
    dialog = OrderDialog.__new__(OrderDialog)
    dialog._line_items = [
        _OrderLineItem(
            order_line_id=7,
            product_variant_id=11,
            product_name="Traditional Shirt",
            sku="SHIRT-001",
            quantity=2,
            unit_price=Decimal("10.00"),
            notes="Existing note",
        )
    ]

    lines = dialog._build_update_line_inputs()

    assert len(lines) == 1
    assert lines[0].order_line_id == 7
    assert lines[0].product_variant_id == 11
    assert lines[0].notes == "Existing note"
