import pytest

from app.application.dto.products import CreateProductInput, CreateProductVariantInput
from app.application.dto.suppliers import CreateSupplierInput, UpdateSupplierInput
from app.application.services.products import CreateProductService, ListProductsService
from app.application.services.suppliers import (
    CreateSupplierService,
    GetSupplierForEditService,
    ListSuppliersService,
    UpdateSupplierService,
)


def test_create_supplier_service_creates_supplier(db_session):
    supplier = CreateSupplierService(db_session).execute(
        CreateSupplierInput(
            name="Tejidos Atlántico",
            tax_id="B12345678",
            phone="+34 600000000",
            email="supplier@example.com",
            address_line_1="Calle Mayor 1",
            postal_code="38001",
            city="Santa Cruz de Tenerife",
            country="Spain",
            notes="Preferred fabric supplier",
        )
    )

    assert supplier.id is not None
    assert supplier.name == "Tejidos Atlántico"
    assert supplier.tax_id == "B12345678"
    assert supplier.is_active is True


def test_list_suppliers_service_returns_suppliers_ordered_by_name(db_session):
    create_service = CreateSupplierService(db_session)
    create_service.execute(CreateSupplierInput(name="Zeta Supplier", city="Adeje"))
    create_service.execute(CreateSupplierInput(name="Alpha Supplier", city="La Laguna"))

    suppliers = ListSuppliersService(db_session).execute()

    assert [supplier.name for supplier in suppliers] == ["Alpha Supplier", "Zeta Supplier"]
    assert suppliers[0].city == "La Laguna"
    assert suppliers[0].is_active is True


def test_get_supplier_for_edit_service_returns_full_supplier_data(db_session):
    supplier = CreateSupplierService(db_session).execute(
        CreateSupplierInput(
            name="Tejidos Atlántico",
            tax_id="B12345678",
            phone="+34 600000000",
            email="supplier@example.com",
            address_line_1="Calle Mayor 1",
            address_line_2="Local 2",
            postal_code="38001",
            city="Santa Cruz de Tenerife",
            country="Spain",
            notes="Preferred fabric supplier",
        )
    )

    result = GetSupplierForEditService(db_session).execute(supplier.id)

    assert result.id == supplier.id
    assert result.name == "Tejidos Atlántico"
    assert result.tax_id == "B12345678"
    assert result.phone == "+34 600000000"
    assert result.email == "supplier@example.com"
    assert result.address_line_1 == "Calle Mayor 1"
    assert result.address_line_2 == "Local 2"
    assert result.postal_code == "38001"
    assert result.city == "Santa Cruz de Tenerife"
    assert result.country == "Spain"
    assert result.notes == "Preferred fabric supplier"
    assert result.is_active is True


def test_update_supplier_service_updates_supplier(db_session):
    supplier = CreateSupplierService(db_session).execute(
        CreateSupplierInput(
            name="Tejidos Atlántico",
            phone="+34 600000000",
            city="Santa Cruz de Tenerife",
        )
    )

    updated = UpdateSupplierService(db_session).execute(
        supplier.id,
        UpdateSupplierInput(
            name="Tejidos del Norte",
            tax_id="B87654321",
            phone="+34 611111111",
            email="north@example.com",
            address_line_1="Camino Norte 5",
            address_line_2=None,
            postal_code="38300",
            city="La Orotava",
            country="Spain",
            notes="Updated supplier",
            is_active=False,
        ),
    )

    assert updated.id == supplier.id
    assert updated.name == "Tejidos del Norte"
    assert updated.tax_id == "B87654321"
    assert updated.phone == "+34 611111111"
    assert updated.email == "north@example.com"
    assert updated.address_line_1 == "Camino Norte 5"
    assert updated.address_line_2 is None
    assert updated.postal_code == "38300"
    assert updated.city == "La Orotava"
    assert updated.country == "Spain"
    assert updated.notes == "Updated supplier"
    assert updated.is_active is False


def test_supplier_services_fail_when_name_is_blank(db_session):
    create_service = CreateSupplierService(db_session)
    update_service = UpdateSupplierService(db_session)

    with pytest.raises(ValueError, match="Supplier name is required."):
        create_service.execute(CreateSupplierInput(name=" "))

    with pytest.raises(ValueError, match="Supplier name is required."):
        update_service.execute(999999, UpdateSupplierInput(name=" "))


def test_supplier_edit_services_fail_when_supplier_does_not_exist(db_session):
    with pytest.raises(ValueError, match="Supplier not found."):
        GetSupplierForEditService(db_session).execute(999999)

    with pytest.raises(ValueError, match="Supplier not found."):
        UpdateSupplierService(db_session).execute(
            999999,
            UpdateSupplierInput(name="Missing Supplier"),
        )


def test_created_supplier_can_be_assigned_to_product(db_session):
    supplier = CreateSupplierService(db_session).execute(
        CreateSupplierInput(name="Tejidos Atlántico")
    )

    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            supplier_id=supplier.id,
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )

    products = ListProductsService(db_session).execute()

    assert len(products) == 1
    assert products[0].id == product.id
    assert products[0].supplier_id == supplier.id
    assert products[0].supplier_name == "Tejidos Atlántico"
