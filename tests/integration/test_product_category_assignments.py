import pytest

from app.application.dto.product_categories import (
    CreateProductCategoryInput,
    UpdateProductCategoryInput,
)
from app.application.dto.products import (
    CreateProductInput,
    CreateProductVariantInput,
    UpdateProductInput,
)
from app.application.services.product_categories import (
    CreateProductCategoryService,
    UpdateProductCategoryService,
)
from app.application.services.products import (
    CreateProductService,
    GetProductForEditService,
    ListProductVariantPickerOptionsService,
    ListProductsService,
    UpdateProductService,
)


def test_create_product_assigns_multiple_categories_in_selected_order(db_session):
    category_service = CreateProductCategoryService(db_session)
    category_c = category_service.execute(CreateProductCategoryInput(name="Category C"))
    category_a = category_service.execute(CreateProductCategoryInput(name="Category A"))

    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            category_ids=[category_c.id, category_a.id],
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )

    edit_item = GetProductForEditService(db_session).execute(product.id)
    listed_product = ListProductsService(db_session).execute()[0]

    assert [category.name for category in edit_item.categories] == ["Category C", "Category A"]
    assert [category.name for category in listed_product.categories] == ["Category C", "Category A"]


def test_product_variant_picker_options_include_category_names(db_session):
    category_service = CreateProductCategoryService(db_session)
    category_c = category_service.execute(CreateProductCategoryInput(name="Category C"))
    category_a = category_service.execute(CreateProductCategoryInput(name="Category A"))
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            category_ids=[category_c.id, category_a.id],
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )

    variants = ListProductVariantPickerOptionsService(db_session).execute()

    selected_variant = next(variant for variant in variants if variant.product_id == product.id)
    assert selected_variant.category_names == ["Category C", "Category A"]


def test_update_product_replaces_categories(db_session):
    category_service = CreateProductCategoryService(db_session)
    shirts = category_service.execute(CreateProductCategoryInput(name="Shirts"))
    pants = category_service.execute(CreateProductCategoryInput(name="Pants"))
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            category_ids=[shirts.id],
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )

    UpdateProductService(db_session).execute(
        product.id,
        UpdateProductInput(category_ids=[pants.id]),
    )

    edit_item = GetProductForEditService(db_session).execute(product.id)

    assert [category.name for category in edit_item.categories] == ["Pants"]


def test_create_product_rejects_inactive_category(db_session):
    category = CreateProductCategoryService(db_session).execute(
        CreateProductCategoryInput(name="Archived", is_active=False)
    )

    with pytest.raises(ValueError, match="must be active"):
        CreateProductService(db_session).execute(
            CreateProductInput(
                name="Camiseta tradicional",
                category_ids=[category.id],
                variants=[CreateProductVariantInput(variant_name="Default")],
            )
        )


def test_update_product_can_preserve_existing_inactive_category(db_session):
    category = CreateProductCategoryService(db_session).execute(
        CreateProductCategoryInput(name="Archived")
    )
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            category_ids=[category.id],
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )
    UpdateProductCategoryService(db_session).execute(
        category.id,
        UpdateProductCategoryInput(name="Archived", is_active=False),
    )

    UpdateProductService(db_session).execute(
        product.id,
        UpdateProductInput(name="Camiseta editada", category_ids=[category.id]),
    )

    edit_item = GetProductForEditService(db_session).execute(product.id)

    assert edit_item.name == "Camiseta editada"
    assert [category.name for category in edit_item.categories] == ["Archived"]
