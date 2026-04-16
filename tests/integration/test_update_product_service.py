from decimal import Decimal

import pytest

from app.application.dto.products import (
    CreateProductInput,
    CreateProductVariantInput,
    UNSET,
    UpdateProductInput,
    UpdateProductVariantInput,
)
from app.application.services.products import (
    CreateProductService,
    GetProductForEditService,
    ListProductsService,
    UpdateProductService,
)
from app.infrastructure.db.models import Supplier


def test_get_product_for_edit_service_returns_product_with_default_variant(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                    size="M",
                    color="White",
                    price_override=Decimal("42.90"),
                )
            ],
        )
    )

    result = GetProductForEditService(db_session).execute(product.id)

    assert result.id == product.id
    assert result.supplier_name is None
    assert result.name == "Camiseta tradicional"
    assert result.default_variant.id == product.variants[0].id
    assert result.default_variant.variant_name == "Default"
    assert result.default_variant.size == "M"
    assert result.default_variant.color == "White"
    assert result.default_variant.price_override == Decimal("42.90")


def test_update_product_service_updates_product_and_default_variant(db_session):
    original_supplier = Supplier(name="Original Supplier")
    updated_supplier = Supplier(name="Updated Supplier")
    db_session.add_all([original_supplier, updated_supplier])
    db_session.flush()

    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            supplier_id=original_supplier.id,
            description="Original description",
            base_price=Decimal("39.90"),
            track_stock=False,
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                    description="Original variant",
                    size="M",
                    color="White",
                    price_override=Decimal("42.90"),
                )
            ],
        )
    )

    default_variant = product.variants[0]

    updated = UpdateProductService(db_session).execute(
        product.id,
        UpdateProductInput(
            name="Camisa bordada",
            supplier_id=updated_supplier.id,
            description="Updated description",
            base_price=Decimal("49.90"),
            track_stock=True,
            default_variant=UpdateProductVariantInput(
                variant_id=default_variant.id,
                variant_name="Default updated",
                description="Updated variant",
                size="L",
                color="Blue",
                price_override=Decimal("55.00"),
            ),
        ),
    )

    assert updated.id == product.id
    assert updated.name == "Camisa bordada"
    assert updated.supplier_id == updated_supplier.id
    assert updated.description == "Updated description"
    assert updated.base_price == Decimal("49.90")
    assert updated.track_stock is True
    assert updated.variants[0].id == default_variant.id
    assert updated.variants[0].sku == default_variant.sku
    assert updated.variants[0].variant_name == "Default updated"
    assert updated.variants[0].description == "Updated variant"
    assert updated.variants[0].size == "L"
    assert updated.variants[0].color == "Blue"
    assert updated.variants[0].price_override == Decimal("55.00")

    listed = ListProductsService(db_session).execute()

    assert len(listed) == 1
    assert listed[0].name == "Camisa bordada"
    assert listed[0].supplier_name == "Updated Supplier"
    assert listed[0].variants[0].variant_name == "Default updated"


def test_update_product_service_preserves_omitted_fields(db_session):
    supplier = Supplier(name="Original Supplier")
    db_session.add(supplier)
    db_session.flush()

    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            supplier_id=supplier.id,
            description="Original description",
            base_price=Decimal("39.90"),
            track_stock=True,
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                    description="Original variant",
                    size="M",
                    color="White",
                    price_override=Decimal("42.90"),
                )
            ],
        )
    )

    default_variant = product.variants[0]

    updated = UpdateProductService(db_session).execute(
        product.id,
        UpdateProductInput(
            name="Camisa bordada",
        ),
    )

    assert updated.name == "Camisa bordada"
    assert updated.supplier_id == supplier.id
    assert updated.description == "Original description"
    assert updated.base_price == Decimal("39.90")
    assert updated.track_stock is True
    assert updated.variants[0].id == default_variant.id
    assert updated.variants[0].variant_name == "Default"
    assert updated.variants[0].description == "Original variant"
    assert updated.variants[0].size == "M"
    assert updated.variants[0].color == "White"
    assert updated.variants[0].price_override == Decimal("42.90")


def test_update_product_service_allows_explicitly_clearing_optional_fields(db_session):
    supplier = Supplier(name="Original Supplier")
    db_session.add(supplier)
    db_session.flush()

    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            supplier_id=supplier.id,
            description="Original description",
            base_price=Decimal("39.90"),
            track_stock=True,
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                    description="Original variant",
                    size="M",
                    color="White",
                    price_override=Decimal("42.90"),
                )
            ],
        )
    )

    updated = UpdateProductService(db_session).execute(
        product.id,
        UpdateProductInput(
            supplier_id=None,
            description=None,
            base_price=None,
            default_variant=UpdateProductVariantInput(
                variant_id=product.variants[0].id,
                variant_name=None,
                description=None,
                size=None,
                color=None,
                price_override=None,
            ),
        ),
    )

    assert updated.supplier_id is None
    assert updated.description is None
    assert updated.base_price is None
    assert updated.track_stock is True
    assert updated.variants[0].variant_name is None
    assert updated.variants[0].description is None
    assert updated.variants[0].size is None
    assert updated.variants[0].color is None
    assert updated.variants[0].price_override is None


def test_update_product_service_preserves_variant_fields_when_omitted(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                    description="Original variant",
                    size="M",
                    color="White",
                    price_override=Decimal("42.90"),
                )
            ],
        )
    )

    updated = UpdateProductService(db_session).execute(
        product.id,
        UpdateProductInput(
            default_variant=UpdateProductVariantInput(
                variant_id=product.variants[0].id,
                variant_name=UNSET,
                description=UNSET,
                size=UNSET,
                color=UNSET,
                price_override=UNSET,
            ),
        ),
    )

    assert updated.variants[0].variant_name == "Default"
    assert updated.variants[0].description == "Original variant"
    assert updated.variants[0].size == "M"
    assert updated.variants[0].color == "White"
    assert updated.variants[0].price_override == Decimal("42.90")


def test_update_product_service_fails_when_product_does_not_exist(db_session):
    service = UpdateProductService(db_session)

    with pytest.raises(ValueError, match="Product not found."):
        service.execute(
            999999,
            UpdateProductInput(
                name="Camisa bordada",
            ),
        )


def test_update_product_service_fails_when_default_variant_does_not_belong_to_product(db_session):
    create_service = CreateProductService(db_session)
    first_product = create_service.execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )
    second_product = create_service.execute(
        CreateProductInput(
            name="Vestido rojo",
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )

    with pytest.raises(ValueError, match="Product variant not found."):
        UpdateProductService(db_session).execute(
            first_product.id,
            UpdateProductInput(
                name="Camisa bordada",
                default_variant=UpdateProductVariantInput(
                    variant_id=second_product.variants[0].id,
                    variant_name="Wrong variant",
                ),
            ),
        )


def test_update_product_service_fails_when_name_is_blank(db_session):
    service = UpdateProductService(db_session)

    with pytest.raises(ValueError, match="Product name is required."):
        service.execute(
            999999,
            UpdateProductInput(
                name=" ",
            ),
        )


def test_update_product_service_fails_when_base_price_is_negative(db_session):
    service = UpdateProductService(db_session)

    with pytest.raises(ValueError, match="Product base price cannot be negative."):
        service.execute(
            999999,
            UpdateProductInput(
                name="Camisa bordada",
                base_price=Decimal("-1.00"),
            ),
        )


@pytest.mark.parametrize("base_price", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_update_product_service_fails_when_base_price_is_not_finite(db_session, base_price):
    service = UpdateProductService(db_session)

    with pytest.raises(ValueError, match="Product base price must be a finite number."):
        service.execute(
            999999,
            UpdateProductInput(
                name="Camisa bordada",
                base_price=base_price,
            ),
        )


def test_update_product_service_fails_when_default_variant_price_override_is_negative(db_session):
    service = UpdateProductService(db_session)

    with pytest.raises(ValueError, match="Default variant price override cannot be negative."):
        service.execute(
            999999,
            UpdateProductInput(
                name="Camisa bordada",
                default_variant=UpdateProductVariantInput(
                    variant_id=1,
                    price_override=Decimal("-1.00"),
                ),
            ),
        )


@pytest.mark.parametrize(
    "price_override",
    [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")],
)
def test_update_product_service_fails_when_default_variant_price_override_is_not_finite(
    db_session,
    price_override,
):
    service = UpdateProductService(db_session)

    with pytest.raises(
        ValueError,
        match="Default variant price override must be a finite number.",
    ):
        service.execute(
            999999,
            UpdateProductInput(
                name="Camisa bordada",
                default_variant=UpdateProductVariantInput(
                    variant_id=1,
                    price_override=price_override,
                ),
            ),
        )
