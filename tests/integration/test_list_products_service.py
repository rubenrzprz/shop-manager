from decimal import Decimal

from app.application.dto.products import CreateProductInput, CreateProductVariantInput
from app.application.services.products import CreateProductService, ListProductsService
from app.infrastructure.db.models import Supplier


def test_list_products_service_returns_created_products_with_variants(db_session):
    supplier = Supplier(
        name="Tejidos Atlántico",
        phone="+34 600000000",
        email="supplier@example.com",
        city="La Orotava",
        country="Spain",
    )
    db_session.add(supplier)
    db_session.flush()

    create_service = CreateProductService(db_session)

    created = create_service.execute(
        CreateProductInput(
            name="Camiseta tradicional",
            supplier_id=supplier.id,
            description="Handcrafted shirt",
            base_price=Decimal("39.90"),
            track_stock=False,
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                    description="Default variant",
                ),
                CreateProductVariantInput(
                    size="M",
                    color="White",
                    variant_name="M / White",
                    description="Variant M / White",
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
    assert product.supplier_id == supplier.id
    assert product.supplier_name == "Tejidos Atlántico"
    assert product.description == "Handcrafted shirt"
    assert product.base_price == Decimal("39.90")
    assert product.track_stock is False
    assert product.is_active is True

    assert len(product.variants) == 2
    assert product.variants[0].sku == f"CAM-{created.id:04d}-01"
    assert product.variants[0].variant_name == "Default"
    assert product.variants[1].sku == f"CAM-{created.id:04d}-02"
    assert product.variants[1].variant_name == "M / White"


def test_list_products_service_returns_empty_list_when_no_products_exist(db_session):
    list_service = ListProductsService(db_session)

    products = list_service.execute()

    assert products == []