from datetime import date
from decimal import Decimal

import pytest

from app.application.dto.customers import CreateCustomerInput
from app.application.dto.orders import (
    CreateOrderInput,
    CreateOrderLineInput,
    UpdateOrderInput,
    UpdateOrderLineInput,
)
from app.application.dto.products import CreateProductInput, CreateProductVariantInput
from app.application.services.customers import CreateCustomerService
from app.application.services.orders import CreateOrderService, UpdateOrderService
from app.application.services.products import CreateProductService
from app.application.services.settings import ApplicationSettingsService
from app.domain.enums import CustomerType, DiscountType, OrderStatus


def create_customer(db_session):
    return CreateCustomerService(db_session).execute(
        CreateCustomerInput(
            customer_type=CustomerType.INDIVIDUAL,
            name="Maria Rodriguez",
            phone="+34 600000000",
        )
    )


def create_product_variant(db_session):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Traditional Shirt",
            base_price=Decimal("49.90"),
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                )
            ],
        )
    )
    return product.variants[0]


def update_input_for_order(order, customer, *, quantity: int = 1, **overrides):
    data = {
        "customer_id": customer.id,
        "order_date": order.order_date,
        "deadline": order.deadline,
        "discount_type": order.discount_type,
        "discount_value": order.discount_value,
        "notes": order.notes,
        "lines": [
            UpdateOrderLineInput(
                order_line_id=line.id,
                product_variant_id=line.product_variant_id,
                quantity=quantity,
                unit_price=line.unit_price,
                notes=line.notes,
            )
            for line in sorted(order.lines, key=lambda order_line: order_line.id)
        ],
    }
    data.update(overrides)
    return UpdateOrderInput(**data)


def create_confirmed_order(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session)
    order = CreateOrderService(db_session).execute(
        CreateOrderInput(
            customer_id=customer.id,
            order_date=date(2026, 4, 19),
            lines=[
                CreateOrderLineInput(
                    product_variant_id=variant.id,
                    quantity=1,
                )
            ],
        )
    )
    order.status = OrderStatus.CONFIRMED
    db_session.flush()
    return order, customer, variant


def test_application_settings_service_defaults_strict_order_workflow_to_false(db_session):
    settings = ApplicationSettingsService(db_session).get_settings()

    assert not settings.strict_order_workflow_enabled


def test_application_settings_service_saves_strict_order_workflow(db_session):
    service = ApplicationSettingsService(db_session)

    service.set_strict_order_workflow_enabled(True)
    db_session.commit()

    assert ApplicationSettingsService(db_session).strict_order_workflow_enabled()

    service.set_strict_order_workflow_enabled(False)
    db_session.commit()

    assert not ApplicationSettingsService(db_session).strict_order_workflow_enabled()


def test_application_settings_service_defaults_app_language_to_english(db_session):
    settings = ApplicationSettingsService(db_session).get_settings()

    assert settings.app_language == "en"


def test_application_settings_service_saves_app_language(db_session):
    service = ApplicationSettingsService(db_session)

    service.set_app_language("es")
    db_session.commit()

    assert ApplicationSettingsService(db_session).app_language() == "es"


def test_application_settings_service_rejects_unsupported_app_language(db_session):
    with pytest.raises(ValueError, match="Application language must be one of: en, es."):
        ApplicationSettingsService(db_session).set_app_language("fr")


def test_order_edit_policy_uses_strict_order_workflow_setting(db_session):
    order, customer, variant = create_confirmed_order(db_session)

    UpdateOrderService(db_session).execute(
        order.id,
        UpdateOrderInput(
            customer_id=customer.id,
            order_date=date(2026, 4, 19),
            lines=[
                UpdateOrderLineInput(
                    product_variant_id=variant.id,
                    quantity=1,
                )
            ],
        ),
    )

    ApplicationSettingsService(db_session).set_strict_order_workflow_enabled(True)
    db_session.commit()

    UpdateOrderService(db_session).execute(
        order.id,
        UpdateOrderInput(
            customer_id=customer.id,
            order_date=date(2026, 4, 19),
            lines=[
                UpdateOrderLineInput(
                    product_variant_id=variant.id,
                    quantity=2,
                )
            ],
        ),
    )

    assert order.lines[0].quantity == 2


def test_strict_order_workflow_allows_ready_deadline_discount_and_notes_only(db_session):
    order, customer, _variant = create_confirmed_order(db_session)
    order.status = OrderStatus.READY
    db_session.flush()
    ApplicationSettingsService(db_session).set_strict_order_workflow_enabled(True)
    db_session.commit()

    UpdateOrderService(db_session).execute(
        order.id,
        update_input_for_order(
            order,
            customer,
            deadline=date(2026, 4, 25),
            discount_type=DiscountType.FIXED,
            discount_value=Decimal("5.00"),
            notes="Ready note",
        ),
    )

    assert order.deadline == date(2026, 4, 25)
    assert order.discount_amount == Decimal("5.00")
    assert order.notes == "Ready note"

    with pytest.raises(ValueError, match="Ready orders cannot change order lines."):
        UpdateOrderService(db_session).execute(
            order.id,
            update_input_for_order(order, customer, quantity=2),
        )


def test_strict_order_workflow_allows_completed_notes_only(db_session):
    order, customer, _variant = create_confirmed_order(db_session)
    order.status = OrderStatus.COMPLETED
    db_session.flush()
    ApplicationSettingsService(db_session).set_strict_order_workflow_enabled(True)
    db_session.commit()

    UpdateOrderService(db_session).execute(
        order.id,
        update_input_for_order(order, customer, notes="Completion note"),
    )

    assert order.notes == "Completion note"

    with pytest.raises(
        ValueError,
        match="Completed and cancelled orders cannot change deadline.",
    ):
        UpdateOrderService(db_session).execute(
            order.id,
            update_input_for_order(order, customer, deadline=date(2026, 4, 26)),
        )


def test_strict_order_workflow_allows_cancelled_notes_only(db_session):
    order, customer, _variant = create_confirmed_order(db_session)
    order.status = OrderStatus.CANCELLED
    db_session.flush()
    ApplicationSettingsService(db_session).set_strict_order_workflow_enabled(True)
    db_session.commit()

    UpdateOrderService(db_session).execute(
        order.id,
        update_input_for_order(order, customer, notes="Cancelled note"),
    )

    assert order.notes == "Cancelled note"

    with pytest.raises(
        ValueError,
        match="Completed and cancelled orders cannot change discount.",
    ):
        UpdateOrderService(db_session).execute(
            order.id,
            update_input_for_order(
                order,
                customer,
                discount_type=DiscountType.FIXED,
                discount_value=Decimal("1.00"),
            ),
        )
