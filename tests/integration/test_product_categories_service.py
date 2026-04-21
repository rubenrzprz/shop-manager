import pytest

from app.application.dto.product_categories import (
    CreateProductCategoryInput,
    UpdateProductCategoryInput,
)
from app.application.services.product_categories import (
    CreateProductCategoryService,
    GetProductCategoryForEditService,
    ListProductCategoriesService,
    ListProductCategoryOptionsService,
    UpdateProductCategoryService,
)


def test_create_product_category_service_creates_category(db_session):
    category = CreateProductCategoryService(db_session).execute(
        CreateProductCategoryInput(
            name="Shirts",
            description="Upper body garments",
        )
    )

    assert category.id is not None
    assert category.name == "Shirts"
    assert category.description == "Upper body garments"
    assert category.is_active is True


def test_create_product_category_service_rejects_duplicate_name_case_insensitive(db_session):
    service = CreateProductCategoryService(db_session)
    service.execute(CreateProductCategoryInput(name="Shirts"))

    with pytest.raises(ValueError, match="already exists"):
        service.execute(CreateProductCategoryInput(name="shirts"))


def test_update_product_category_service_updates_category(db_session):
    category = CreateProductCategoryService(db_session).execute(
        CreateProductCategoryInput(name="Shirts")
    )

    updated = UpdateProductCategoryService(db_session).execute(
        category.id,
        UpdateProductCategoryInput(
            name="Tops",
            description="All upper body garments",
            is_active=False,
        ),
    )

    assert updated.name == "Tops"
    assert updated.description == "All upper body garments"
    assert updated.is_active is False


def test_list_and_get_product_category_services_return_dtos(db_session):
    category = CreateProductCategoryService(db_session).execute(
        CreateProductCategoryInput(name="Shirts")
    )

    listed = ListProductCategoriesService(db_session).execute()
    options = ListProductCategoryOptionsService(db_session).execute()
    edit_item = GetProductCategoryForEditService(db_session).execute(category.id)

    assert [item.name for item in listed] == ["Shirts"]
    assert [item.name for item in options] == ["Shirts"]
    assert edit_item.name == "Shirts"
