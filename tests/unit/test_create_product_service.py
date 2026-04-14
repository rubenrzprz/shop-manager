from decimal import Decimal

import pytest

from app.application.dto.products import CreateProductInput, CreateProductVariantInput
from app.application.services.products import CreateProductService


class StubSession:
    def __init__(self) -> None:
        self._next_product_id = 1
        self._added: list[object] = []
        self._deleted: list[object] = []

    def add(self, instance) -> None:
        self._added.append(instance)

    def delete(self, instance) -> None:
        self._deleted.append(instance)

    def flush(self) -> None:
        for instance in self._added:
            if hasattr(instance, "id") and getattr(instance, "id", None) is None:
                setattr(instance, "id", self._next_product_id)
                self._next_product_id += 1


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


@pytest.mark.parametrize("base_price", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_create_product_service_fails_when_base_price_is_not_finite(base_price):
    service = CreateProductService(session=None)  # type: ignore[arg-type]

    data = CreateProductInput(
        name="Camiseta tradicional",
        base_price=base_price,
        variants=[
            CreateProductVariantInput(
                variant_name="Default",
            )
        ],
    )

    with pytest.raises(ValueError, match="Product base price must be a finite number."):
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


@pytest.mark.parametrize(
    "price_override",
    [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")],
)
def test_create_product_service_fails_when_variant_price_override_is_not_finite(price_override):
    service = CreateProductService(session=None)  # type: ignore[arg-type]

    data = CreateProductInput(
        name="Camiseta tradicional",
        variants=[
            CreateProductVariantInput(
                variant_name="Variant A",
                price_override=price_override,
            ),
        ],
    )

    with pytest.raises(ValueError, match="Variant #1 price override must be a finite number."):
        service.execute(data)


def test_create_product_service_persists_normalized_variant_sku():
    service = CreateProductService(session=StubSession())  # type: ignore[arg-type]

    data = CreateProductInput(
        name="Camiseta tradicional",
        variants=[
            CreateProductVariantInput(
                sku=" SKU-001 ",
                variant_name="Variant A",
            ),
        ],
    )

    product = service.execute(data)

    assert product.variants[0].sku == "SKU-001"


def test_create_product_service_fails_when_provided_sku_collides_with_generated_sku():
    session = StubSession()
    service = CreateProductService(session=session)  # type: ignore[arg-type]

    data = CreateProductInput(
        name="Camiseta tradicional",
        variants=[
            CreateProductVariantInput(
                sku="CAM-0001-02",
                variant_name="Variant A",
            ),
            CreateProductVariantInput(
                variant_name="Variant B",
            ),
        ],
    )

    with pytest.raises(ValueError, match="Variant SKUs must be unique within the request."):
        service.execute(data)

    assert len(session._deleted) == 1
