import pytest

import app.ui.dialogs.product_dialog as product_dialog_module
from app.application.dto.products import CreateProductVariantInput
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


def test_add_variant_to_existing_product_stays_pending(monkeypatch):
    dialog = ProductDialog.__new__(ProductDialog)
    dialog._product_id = 10
    dialog._variant_drafts = []
    table_refreshed = False

    class FakeVariantDialog:
        variant_input = CreateProductVariantInput(variant_name="Blue", size="M")

        def __init__(self, parent):
            self.parent = parent

        def exec(self):
            return True

    def fail_session():
        raise AssertionError("variant actions must not open a session before Save")

    def refresh_table():
        nonlocal table_refreshed
        table_refreshed = True

    monkeypatch.setattr(product_dialog_module, "ProductVariantDialog", FakeVariantDialog)
    monkeypatch.setattr(product_dialog_module, "SessionLocal", fail_session)
    dialog._populate_saved_variants_table = refresh_table

    ProductDialog._add_variant(dialog)

    assert table_refreshed
    assert len(dialog._variant_drafts) == 1
    assert dialog._variant_drafts[0].id is None
    assert dialog._variant_drafts[0].variant_name == "Blue"
    assert dialog._variant_drafts[0].size == "M"


def test_product_dialog_category_selection_reads_draggable_list_order():
    dialog = ProductDialog.__new__(ProductDialog)
    dialog._selected_category_ids = []

    class FakeItem:
        def __init__(self, category_id):
            self._category_id = category_id

        def data(self, _role):
            return self._category_id

    class FakeSelectedCategoryList:
        def __init__(self):
            self.category_ids = [3, 1]

        def count(self):
            return len(self.category_ids)

        def item(self, row):
            return FakeItem(self.category_ids[row])

        def takeItem(self, row):
            self.category_ids.pop(row)

    dialog._selected_categories_list = FakeSelectedCategoryList()
    dialog._populate_categories_table = lambda: None

    assert ProductDialog._selected_category_ids_from_table(dialog) == [3, 1]

    ProductDialog._remove_category(dialog, 3)

    assert ProductDialog._selected_category_ids_from_table(dialog) == [1]


def test_pending_variant_changes_are_applied_on_save(monkeypatch):
    calls = []
    session = object()
    dialog = ProductDialog.__new__(ProductDialog)
    dialog._product_id = 10
    dialog._variant_drafts = [
        product_dialog_module._VariantDraft(
            id=1,
            sku="TSHIRT-10-1",
            size="M",
            color="Red",
            variant_name="Red / M",
            description=None,
            price_override=None,
            stock_current=3,
            stock_minimum=1,
            is_active=False,
            original_is_active=True,
        ),
        product_dialog_module._VariantDraft(
            id=None,
            sku=None,
            size="L",
            color="Blue",
            variant_name="Blue / L",
            description=None,
            price_override=None,
            stock_current=None,
            stock_minimum=None,
            is_active=True,
        ),
    ]

    class FakeCreateProductVariantService:
        def __init__(self, service_session):
            assert service_session is session

        def execute(self, product_id, data):
            calls.append(("create", product_id, data.variant_name, data.is_active))

    class FakeUpdateProductVariantService:
        def __init__(self, service_session):
            assert service_session is session

        def execute(self, variant_id, data):
            calls.append(("update", variant_id, data.variant_name, data.stock_current))

    class FakeProductVariantStatusService:
        def __init__(self, service_session):
            assert service_session is session

        def execute(self, variant_id, is_active):
            calls.append(("status", variant_id, is_active))

    monkeypatch.setattr(
        product_dialog_module,
        "CreateProductVariantService",
        FakeCreateProductVariantService,
    )
    monkeypatch.setattr(
        product_dialog_module,
        "UpdateProductVariantService",
        FakeUpdateProductVariantService,
    )
    monkeypatch.setattr(
        product_dialog_module,
        "ProductVariantStatusService",
        FakeProductVariantStatusService,
    )

    ProductDialog._apply_pending_variant_changes(dialog, session)

    assert calls == [
        ("update", 1, "Red / M", 3),
        ("create", 10, "Blue / L", True),
        ("status", 1, False),
    ]


def test_pending_variant_status_swap_activates_before_deactivating(monkeypatch):
    calls = []
    session = object()
    dialog = ProductDialog.__new__(ProductDialog)
    dialog._product_id = 10
    dialog._variant_drafts = [
        product_dialog_module._VariantDraft(
            id=1,
            sku="TSHIRT-10-1",
            size=None,
            color=None,
            variant_name="Old active",
            description=None,
            price_override=None,
            stock_current=None,
            stock_minimum=None,
            is_active=False,
            original_is_active=True,
        ),
        product_dialog_module._VariantDraft(
            id=2,
            sku="TSHIRT-10-2",
            size=None,
            color=None,
            variant_name="New active",
            description=None,
            price_override=None,
            stock_current=None,
            stock_minimum=None,
            is_active=True,
            original_is_active=False,
        ),
    ]

    class FakeCreateProductVariantService:
        def __init__(self, service_session):
            assert service_session is session

        def execute(self, product_id, data):
            calls.append(("create", product_id, data.variant_name, data.is_active))

    class FakeUpdateProductVariantService:
        def __init__(self, service_session):
            assert service_session is session

        def execute(self, variant_id, data):
            calls.append(("update", variant_id, data.variant_name))

    class FakeProductVariantStatusService:
        def __init__(self, service_session):
            assert service_session is session

        def execute(self, variant_id, is_active):
            calls.append(("status", variant_id, is_active))

    monkeypatch.setattr(
        product_dialog_module,
        "CreateProductVariantService",
        FakeCreateProductVariantService,
    )
    monkeypatch.setattr(
        product_dialog_module,
        "UpdateProductVariantService",
        FakeUpdateProductVariantService,
    )
    monkeypatch.setattr(
        product_dialog_module,
        "ProductVariantStatusService",
        FakeProductVariantStatusService,
    )

    ProductDialog._apply_pending_variant_changes(dialog, session)

    assert calls == [
        ("update", 1, "Old active"),
        ("update", 2, "New active"),
        ("status", 2, True),
        ("status", 1, False),
    ]
