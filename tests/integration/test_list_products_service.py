from decimal import Decimal

from app.application.dto.product_categories import CreateProductCategoryInput
from app.application.dto.products import (
    CreateProductInput,
    CreateProductVariantInput,
    ProductListFilters,
)
from app.application.services.product_categories import CreateProductCategoryService
from app.application.services.products import (
    CreateProductService,
    ListProductVariantPickerOptionsService,
    ListProductsService,
)
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


def test_list_products_service_filters_by_category_and_uncategorized(db_session):
    category_service = CreateProductCategoryService(db_session)
    shirts = category_service.execute(CreateProductCategoryInput(name="Shirts"))
    pants = category_service.execute(CreateProductCategoryInput(name="Pants"))
    create_service = CreateProductService(db_session)
    create_service.execute(
        CreateProductInput(
            name="Linen Shirt",
            category_ids=[shirts.id],
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )
    create_service.execute(
        CreateProductInput(
            name="Work Pants",
            category_ids=[pants.id],
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )
    create_service.execute(
        CreateProductInput(
            name="Gift Card",
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )

    list_service = ListProductsService(db_session)

    assert [
        product.name
        for product in list_service.execute(ProductListFilters(category_id=shirts.id))
    ] == ["Linen Shirt"]
    assert [
        product.name
        for product in list_service.execute(ProductListFilters(uncategorized_only=True))
    ] == ["Gift Card"]


def test_list_products_service_search_matches_product_supplier_variant_and_category(
    db_session,
):
    supplier = Supplier(name="North Textiles")
    db_session.add(supplier)
    db_session.flush()
    category = CreateProductCategoryService(db_session).execute(
        CreateProductCategoryInput(name="Ceremony")
    )
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Linen Shirt",
            supplier_id=supplier.id,
            category_ids=[category.id],
            variants=[
                CreateProductVariantInput(
                    sku="LINEN-BLUE-M",
                    variant_name="Blue Medium",
                    size="M",
                    color="Blue",
                )
            ],
        )
    )
    CreateProductService(db_session).execute(
        CreateProductInput(
            name="Work Pants",
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )

    list_service = ListProductsService(db_session)

    for query in ["linen", "north", "ceremony", "blue medium", "medium", "blue"]:
        products = list_service.execute(ProductListFilters(search_text=query))
        assert [listed_product.id for listed_product in products] == [product.id]


def test_list_products_service_search_treats_like_wildcards_as_literals(db_session):
    create_service = CreateProductService(db_session)
    literal_underscore_product = create_service.execute(
        CreateProductInput(
            name="Literal Underscore",
            variants=[CreateProductVariantInput(sku="ABC_123", variant_name="Default")],
        )
    )
    create_service.execute(
        CreateProductInput(
            name="Wildcard Candidate",
            variants=[CreateProductVariantInput(sku="ABCX123", variant_name="Default")],
        )
    )
    literal_percent_product = create_service.execute(
        CreateProductInput(
            name="Ten Percent Discount",
            variants=[CreateProductVariantInput(variant_name="10% off")],
        )
    )
    create_service.execute(
        CreateProductInput(
            name="Ten Points Discount",
            variants=[CreateProductVariantInput(variant_name="10 points off")],
        )
    )

    list_service = ListProductsService(db_session)

    assert [
        product.id
        for product in list_service.execute(ProductListFilters(search_text="abc_123"))
    ] == [literal_underscore_product.id]
    assert [
        product.id for product in list_service.execute(ProductListFilters(search_text="%"))
    ] == [literal_percent_product.id]


def test_list_product_variant_picker_options_service_returns_variant_selection_data(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Traditional Shirt",
            base_price=Decimal("49.90"),
            variants=[
                CreateProductVariantInput(
                    sku="SHIRT-001",
                    variant_name="Size M / White",
                    size="M",
                    color="White",
                    price_override=Decimal("54.50"),
                )
            ],
        )
    )

    options = ListProductVariantPickerOptionsService(db_session).execute()

    assert len(options) == 1
    assert options[0].id == product.variants[0].id
    assert options[0].product_id == product.id
    assert options[0].product_name == "Traditional Shirt"
    assert options[0].sku == "SHIRT-001"
    assert options[0].variant_name == "Size M / White"
    assert options[0].size == "M"
    assert options[0].color == "White"
    assert options[0].price == Decimal("54.50")
    assert options[0].product_is_active is True
    assert options[0].variant_is_active is True


def test_list_product_variant_picker_options_service_preserves_missing_price(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Unpriced Product",
            base_price=None,
            variants=[
                CreateProductVariantInput(
                    sku="UNPRICED-001",
                    variant_name="Default",
                    price_override=None,
                )
            ],
        )
    )

    options = ListProductVariantPickerOptionsService(db_session).execute()

    assert len(options) == 1
    assert options[0].id == product.variants[0].id
    assert options[0].price is None
