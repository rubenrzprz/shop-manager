from decimal import Decimal

import pytest

from app.application.dto.products import CreateProductInput, CreateProductVariantInput
from app.application.services.products import CreateProductService


def test_create_product_service_fails_when_name_is_blank():
    service = CreateProductService(session=None)  # type: ignore[arg-type]

    data = CreateProductInput(
        name="   ",
        variants=[
            CreateProductVariantInput(
                variant_name="Default",
            )
        ],
    )

    with pytest.raises(ValueError, match="Product name is required."):
        service.execute(data)


def test_create_product_service_fails_when_no_variants_are_provided():
    service = CreateProductService(session=None)  # type: ignore[arg-type]

    data = CreateProductInput(
        name="Camiseta tradicional",
        variants=[],
    )

    with pytest.raises(ValueError, match="A product must have at least one variant."):
        service.execute(data)


def test_create_product_service_fails_when_base_price_is_negative():
    service = CreateProductService(session=None)  # type: ignore[arg-type]

    data = CreateProductInput(
        name="Camiseta tradicional",
        base_price=Decimal("-1.00"),
        variants=[
            CreateProductVariantInput(
                variant_name="Default",
            )
        ],
    )

    with pytest.raises(ValueError, match="Product base price cannot be negative."):
        service.execute(data)


def test_create_product_service_fails_when_duplicate_variant_skus_are_provided():
    service = CreateProductService(session=None)  # type: ignore[arg-type]

    data = CreateProductInput(
        name="Camiseta tradicional",
        variants=[
            CreateProductVariantInput(
                sku="CAM-9999-01",
                variant_name="Variant A",
            ),
            CreateProductVariantInput(
                sku="CAM-9999-01",
                variant_name="Variant B",
            ),
        ],
    )

    with pytest.raises(ValueError, match="Variant SKUs must be unique within the request."):
        service.execute(data)


def test_create_product_service_fails_when_variant_sku_is_blank():
    service = CreateProductService(session=None)  # type: ignore[arg-type]

    data = CreateProductInput(
        name="Camiseta tradicional",
        variants=[
            CreateProductVariantInput(
                sku="   ",
                variant_name="Variant A",
            ),
        ],
    )

    with pytest.raises(ValueError, match="Variant #1 SKU cannot be blank."):
        service.execute(data)
