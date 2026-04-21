import pytest

from app.application.dto.products import CreateProductInput, CreateProductVariantInput
from app.application.services.products import (
    CreateProductService,
    ListProductsService,
    ProductStatusService,
    ProductVariantStatusService,
)


def test_product_status_service_marks_product_inactive(db_session):
    create_service = CreateProductService(db_session)
    product = create_service.execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                )
            ],
        )
    )

    service = ProductStatusService(db_session)
    deactivated = service.execute(product.id, is_active=False)

    assert deactivated.id == product.id
    assert deactivated.is_active is False

    products = ListProductsService(db_session).execute()

    assert len(products) == 1
    assert products[0].id == product.id
    assert products[0].is_active is False


def test_product_status_service_deactivates_product_variants(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[
                CreateProductVariantInput(variant_name="Default"),
                CreateProductVariantInput(variant_name="Second"),
            ],
        )
    )

    ProductStatusService(db_session).execute(product.id, is_active=False)
    db_session.flush()

    assert product.is_active is False
    assert [variant.is_active for variant in product.variants] == [False, False]


def test_product_status_service_marks_product_active(db_session):
    create_service = CreateProductService(db_session)
    product = create_service.execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                )
            ],
        )
    )

    service = ProductStatusService(db_session)
    service.execute(product.id, is_active=False)
    ProductVariantStatusService(db_session).execute(product.variants[0].id, is_active=True)
    activated = service.execute(product.id, is_active=True)

    assert activated.id == product.id
    assert activated.is_active is True

    products = ListProductsService(db_session).execute()

    assert len(products) == 1
    assert products[0].id == product.id
    assert products[0].is_active is True


def test_product_status_service_activates_selected_variants_with_product(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[
                CreateProductVariantInput(variant_name="Default"),
                CreateProductVariantInput(variant_name="Second"),
            ],
        )
    )

    service = ProductStatusService(db_session)
    service.execute(product.id, is_active=False)
    activated = service.execute(
        product.id,
        is_active=True,
        active_variant_ids=[product.variants[1].id],
    )

    assert activated.is_active is True
    assert [variant.is_active for variant in product.variants] == [False, True]


def test_product_status_service_requires_selected_variant_when_activating(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[CreateProductVariantInput(variant_name="Default")],
        )
    )

    service = ProductStatusService(db_session)
    service.execute(product.id, is_active=False)

    with pytest.raises(ValueError, match="Select at least one product variant"):
        service.execute(product.id, is_active=True, active_variant_ids=[])


def test_product_status_service_fails_when_product_does_not_exist(db_session):
    service = ProductStatusService(db_session)

    with pytest.raises(ValueError, match="Product not found."):
        service.execute(999999, is_active=False)


def test_product_status_service_fails_when_product_is_already_inactive(db_session):
    create_service = CreateProductService(db_session)
    product = create_service.execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                )
            ],
        )
    )

    service = ProductStatusService(db_session)
    service.execute(product.id, is_active=False)

    with pytest.raises(ValueError, match="Product is already inactive."):
        service.execute(product.id, is_active=False)


def test_product_status_service_fails_when_product_is_already_active(db_session):
    create_service = CreateProductService(db_session)
    product = create_service.execute(
        CreateProductInput(
            name="Camiseta tradicional",
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                )
            ],
        )
    )

    service = ProductStatusService(db_session)

    with pytest.raises(ValueError, match="Product is already active."):
        service.execute(product.id, is_active=True)
