from decimal import Decimal

import pytest

from app.application.dto.products import (
    CreateProductInput,
    CreateProductVariantInput,
    UpdateProductVariantInput,
)
from app.application.services.products import (
    CreateProductService,
    CreateProductVariantService,
    GetProductForEditService,
    ProductStatusService,
    ProductVariantStatusService,
    UpdateProductVariantService,
)


def test_create_product_variant_service_adds_variant_with_next_sku(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )

    variant = CreateProductVariantService(db_session).execute(
        product.id,
        CreateProductVariantInput(
            variant_name="Large / White",
            size="L",
            color="White",
            price_override=Decimal("45.00"),
        ),
    )

    assert variant.product_id == product.id
    assert variant.sku == f"CAM-{product.id:04d}-02"
    assert variant.variant_name == "Large / White"
    assert variant.price_override == Decimal("45.00")


def test_create_product_variant_service_generates_unique_skus_for_pending_variants(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )
    service = CreateProductVariantService(db_session)

    second = service.execute(product.id, CreateProductVariantInput(variant_name="Second"))
    third = service.execute(product.id, CreateProductVariantInput(variant_name="Third"))

    assert second.sku == f"CAM-{product.id:04d}-02"
    assert third.sku == f"CAM-{product.id:04d}-03"


def test_create_product_variant_service_does_not_activate_inactive_product(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            is_active=False,
            variants=[CreateProductVariantInput(variant_name="Default", is_active=False)],
        )
    )

    CreateProductVariantService(db_session).execute(
        product.id,
        CreateProductVariantInput(variant_name="Active variant", is_active=True),
    )
    db_session.flush()

    assert product.is_active is False


def test_update_product_variant_service_updates_variant_fields(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )
    variant = product.variants[0]

    updated = UpdateProductVariantService(db_session).execute(
        variant.id,
        UpdateProductVariantInput(
            variant_id=variant.id,
            variant_name="Updated",
            size="L",
            color="Blue",
            description="Updated variant",
            price_override=Decimal("55.00"),
            stock_current=10,
            stock_minimum=2,
        ),
    )

    assert updated.variant_name == "Updated"
    assert updated.size == "L"
    assert updated.color == "Blue"
    assert updated.description == "Updated variant"
    assert updated.price_override == Decimal("55.00")
    assert updated.stock_current == 10
    assert updated.stock_minimum == 2


def test_product_variant_status_service_deactivates_last_variant_and_product(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )
    variant = product.variants[0]

    ProductVariantStatusService(db_session).execute(variant.id, is_active=False)
    db_session.flush()

    assert variant.is_active is False
    assert product.is_active is False


def test_product_variant_status_service_keeps_product_active_with_another_active_variant(
    db_session,
):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[
                CreateProductVariantInput(variant_name="Default"),
                CreateProductVariantInput(variant_name="Second"),
            ],
        )
    )

    ProductVariantStatusService(db_session).execute(product.variants[0].id, is_active=False)
    db_session.flush()

    assert product.variants[0].is_active is False
    assert product.is_active is True


def test_product_status_service_rejects_activation_without_active_variants(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[CreateProductVariantInput(variant_name="Default", is_active=False)],
        )
    )

    assert product.is_active is False
    with pytest.raises(ValueError, match="at least one active variant"):
        ProductStatusService(db_session).execute(product.id, is_active=True)


def test_get_product_for_edit_service_returns_all_variants(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[
                CreateProductVariantInput(variant_name="Default"),
                CreateProductVariantInput(variant_name="Second", is_active=False),
            ],
        )
    )

    result = GetProductForEditService(db_session).execute(product.id)

    assert [variant.id for variant in result.variants] == [
        product.variants[0].id,
        product.variants[1].id,
    ]
    assert result.variants[0].is_active is True
    assert result.variants[1].is_active is False
