from decimal import Decimal

from app.application.dto.customers import CustomerPickerItem
from app.application.dto.products import ProductVariantPickerItem
from app.domain.enums import CustomerType
from app.ui.dialogs.customer_picker_dialog import CustomerPickerDialog
from app.ui.dialogs.product_variant_picker_dialog import ProductVariantPickerDialog


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
    )

    assert ProductVariantPickerDialog._matches_variant(variant, "traditional")
    assert ProductVariantPickerDialog._matches_variant(variant, "shirt-001")
    assert ProductVariantPickerDialog._matches_variant(variant, "size m")
    assert ProductVariantPickerDialog._matches_variant(variant, "m")
    assert ProductVariantPickerDialog._matches_variant(variant, "white")
    assert not ProductVariantPickerDialog._matches_variant(variant, "supplier")
