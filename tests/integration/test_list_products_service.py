from decimal import Decimal

from app.application.dto.products import CreateProductInput, CreateProductVariantInput
from app.application.services.products import CreateProductService, ListProductsService


def test_list_products_service_returns_created_products_with_variants(db_session):
    create_service = CreateProductService(db_session)

    created = create_service.execute(
        CreateProductInput(
            name="Camiseta tradicional",
            description="Handcrafted shirt",
            base_price=Decimal("39.90"),
            track_stock=False,
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                ),
                CreateProductVariantInput(
                    size="M",
                    color="White",
                    variant_name="M / White",
                    price_override=Decimal("42.90"),
                ),
            ],
        )
    )

    db_session.flush()

    list_service = ListProductsService(db_session)
    products = list_service.execute()

    assert len(products) == 1

    product = products[0]
    assert product.id == created.id
    assert product.name == "Camiseta tradicional"
    assert product.description == "Handcrafted shirt"
    assert product.base_price == Decimal("39.90")
    assert product.track_stock is False
    assert product.is_active is True

    assert len(product.variants) == 2
    assert product.variants[0].sku == f"CAM-{created.id:04d}-01"
    assert product.variants[1].sku == f"CAM-{created.id:04d}-02"


def test_list_products_service_returns_empty_list_when_no_products_exist(db_session):
    list_service = ListProductsService(db_session)

    products = list_service.execute()

    assert products == []