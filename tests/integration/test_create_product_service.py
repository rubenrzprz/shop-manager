from decimal import Decimal

import pytest

from app.application.dto.products import CreateProductInput, CreateProductVariantInput
from app.application.services.products import CreateProductService
from app.infrastructure.db.models import Supplier


def test_create_product_service_fails_without_variants(db_session):
    service = CreateProductService(db_session)

    with pytest.raises(ValueError, match="A product must have at least one variant."):
        service.execute(CreateProductInput(name="Camiseta tradicional", variants=[]))


def test_create_product_service_creates_product_with_default_variant(db_session):
    supplier = Supplier(
        name="Tejidos Atlántico",
        phone="+34 600000010",
        email="supplier@example.com",
        city="La Orotava",
        country="Spain",
    )
    db_session.add(supplier)
    db_session.flush()

    service = CreateProductService(db_session)

    data = CreateProductInput(
        name="Camiseta tradicional",
        supplier_id=supplier.id,
        description="Handcrafted product",
        base_price=Decimal("39.90"),
        track_stock=False,
        variants=[
            CreateProductVariantInput(
                sku=None,
                size=None,
                color=None,
                variant_name="Default",
                description="Default variant",
                price_override=None,
                stock_current=None,
                stock_minimum=None,
            )
        ],
    )

    product = service.execute(data)
    db_session.flush()

    assert product.id is not None
    assert product.name == "Camiseta tradicional"
    assert product.supplier_id == supplier.id
    assert len(product.variants) == 1

    variant = product.variants[0]
    assert variant.id is not None
    assert variant.product_id == product.id
    assert variant.sku == f"CAM-{product.id:04d}-01"


def test_create_product_service_generates_incremental_variant_skus(db_session):
    service = CreateProductService(db_session)

    data = CreateProductInput(
        name="Vestido rojo",
        variants=[
            CreateProductVariantInput(
                sku=None,
                size="S",
                color="Red",
                variant_name="Small / Red",
            ),
            CreateProductVariantInput(
                sku=None,
                size="M",
                color="Red",
                variant_name="Medium / Red",
            ),
        ],
    )

    product = service.execute(data)
    db_session.flush()

    assert len(product.variants) == 2
    assert product.variants[0].sku == f"VES-{product.id:04d}-01"
    assert product.variants[1].sku == f"VES-{product.id:04d}-02"
