from datetime import date
from decimal import Decimal

import pytest

from app.application.dto.customers import CreateCustomerInput
from app.application.dto.orders import CreateOrderInput, CreateOrderLineInput, UpdateOrderInput
from app.application.dto.products import CreateProductInput, CreateProductVariantInput
from app.application.services.customers import CreateCustomerService
from app.application.services.orders import (
    CreateOrderService,
    GetOrderForEditService,
    ListOrdersService,
    UpdateOrderService,
)
from app.application.services.products import CreateProductService
from app.domain.enums import CustomerType, DiscountType, OrderStatus
from app.infrastructure.db.models import Order


def create_customer(db_session, *, is_active: bool = True):
    return CreateCustomerService(db_session).execute(
        CreateCustomerInput(
            customer_type=CustomerType.INDIVIDUAL,
            name="María Rodríguez",
            phone="+34 600000000",
            is_active=is_active,
        )
    )


def create_product_variant(
    db_session,
    *,
    product_is_active: bool = True,
    variant_is_active: bool = True,
    base_price: Decimal | None = Decimal("49.90"),
    price_override: Decimal | None = None,
):
    product = CreateProductService(db_session).execute(
        CreateProductInput(
            name="Traditional Shirt",
            base_price=base_price,
            is_active=product_is_active,
            variants=[
                CreateProductVariantInput(
                    variant_name="Default",
                    price_override=price_override,
                    is_active=variant_is_active,
                )
            ],
        )
    )
    return product.variants[0]


def test_create_order_service_creates_draft_order_with_calculated_totals(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session, price_override=Decimal("54.50"))

    order = CreateOrderService(db_session).execute(
        CreateOrderInput(
            customer_id=customer.id,
            order_date=date(2026, 4, 16),
            deadline=date(2026, 4, 30),
            notes="First order",
            lines=[
                CreateOrderLineInput(
                    product_variant_id=variant.id,
                    quantity=2,
                )
            ],
        )
    )

    assert order.id is not None
    assert order.order_number == f"ORD-{order.id:06d}"
    assert order.customer_id == customer.id
    assert order.status == OrderStatus.DRAFT
    assert order.subtotal_amount == Decimal("109.00")
    assert order.discount_type == DiscountType.NONE
    assert order.discount_value == Decimal("0.00")
    assert order.discount_amount == Decimal("0.00")
    assert order.total_amount == Decimal("109.00")
    assert len(order.lines) == 1
    assert order.lines[0].product_variant_id == variant.id
    assert order.lines[0].quantity == 2
    assert order.lines[0].unit_price == Decimal("54.50")
    assert order.lines[0].line_total == Decimal("109.00")


def test_create_order_service_supports_fixed_discount(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session, base_price=Decimal("80.00"))

    order = CreateOrderService(db_session).execute(
        CreateOrderInput(
            customer_id=customer.id,
            order_date=date(2026, 4, 16),
            discount_type=DiscountType.FIXED,
            discount_value=Decimal("15.00"),
            lines=[
                CreateOrderLineInput(
                    product_variant_id=variant.id,
                    quantity=1,
                )
            ],
        )
    )

    assert order.subtotal_amount == Decimal("80.00")
    assert order.discount_amount == Decimal("15.00")
    assert order.total_amount == Decimal("65.00")


def test_create_order_service_supports_percentage_discount(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session, base_price=Decimal("80.00"))

    order = CreateOrderService(db_session).execute(
        CreateOrderInput(
            customer_id=customer.id,
            order_date=date(2026, 4, 16),
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("12.5"),
            lines=[
                CreateOrderLineInput(
                    product_variant_id=variant.id,
                    quantity=2,
                )
            ],
        )
    )

    assert order.subtotal_amount == Decimal("160.00")
    assert order.discount_amount == Decimal("20.00")
    assert order.total_amount == Decimal("140.00")


def test_create_order_service_uses_normalized_percentage_discount_for_calculation(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session, base_price=Decimal("100.00"))

    order = CreateOrderService(db_session).execute(
        CreateOrderInput(
            customer_id=customer.id,
            order_date=date(2026, 4, 16),
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("12.345"),
            lines=[
                CreateOrderLineInput(
                    product_variant_id=variant.id,
                    quantity=1,
                )
            ],
        )
    )

    assert order.discount_value == Decimal("12.35")
    assert order.discount_amount == Decimal("12.35")
    assert order.total_amount == Decimal("87.65")


def test_list_orders_service_returns_orders_with_customer_and_lines(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session, base_price=Decimal("49.90"))
    order = CreateOrderService(db_session).execute(
        CreateOrderInput(
            customer_id=customer.id,
            order_date=date(2026, 4, 16),
            lines=[
                CreateOrderLineInput(
                    product_variant_id=variant.id,
                    quantity=1,
                )
            ],
        )
    )

    orders = ListOrdersService(db_session).execute()

    assert len(orders) == 1
    assert orders[0].id == order.id
    assert orders[0].order_number == order.order_number
    assert orders[0].customer_id == customer.id
    assert orders[0].customer_name == "María Rodríguez"
    assert orders[0].status == OrderStatus.DRAFT
    assert orders[0].total_amount == Decimal("49.90")
    assert len(orders[0].lines) == 1
    assert orders[0].lines[0].product_name == "Traditional Shirt"
    assert orders[0].lines[0].sku == variant.sku


def test_get_order_for_edit_service_returns_draft_order_details(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session, base_price=Decimal("49.90"))
    order = CreateOrderService(db_session).execute(
        CreateOrderInput(
            customer_id=customer.id,
            order_date=date(2026, 4, 16),
            deadline=date(2026, 4, 30),
            notes="Draft notes",
            lines=[
                CreateOrderLineInput(
                    product_variant_id=variant.id,
                    quantity=2,
                )
            ],
        )
    )

    edit_item = GetOrderForEditService(db_session).execute(order.id)

    assert edit_item.id == order.id
    assert edit_item.order_number == order.order_number
    assert edit_item.customer_id == customer.id
    assert edit_item.customer_name == "María Rodríguez"
    assert edit_item.status == OrderStatus.DRAFT
    assert edit_item.deadline == date(2026, 4, 30)
    assert edit_item.notes == "Draft notes"
    assert len(edit_item.lines) == 1
    assert edit_item.lines[0].product_variant_id == variant.id
    assert edit_item.lines[0].quantity == 2


def test_update_order_service_updates_active_order_fields_lines_and_totals(db_session):
    customer = create_customer(db_session)
    replacement_customer = CreateCustomerService(db_session).execute(
        CreateCustomerInput(
            customer_type=CustomerType.INDIVIDUAL,
            name="Carlos Pérez",
            phone="+34 600000002",
        )
    )
    original_variant = create_product_variant(db_session, base_price=Decimal("49.90"))
    replacement_variant = create_product_variant(db_session, base_price=Decimal("25.00"))
    order = CreateOrderService(db_session).execute(
        CreateOrderInput(
            customer_id=customer.id,
            order_date=date(2026, 4, 16),
            lines=[
                CreateOrderLineInput(
                    product_variant_id=original_variant.id,
                    quantity=1,
                )
            ],
        )
    )

    order.status = OrderStatus.CONFIRMED
    db_session.flush()

    updated_order = UpdateOrderService(db_session).execute(
        order.id,
        UpdateOrderInput(
            customer_id=replacement_customer.id,
            order_date=date(2026, 4, 17),
            deadline=date(2026, 5, 1),
            discount_type=DiscountType.FIXED,
            discount_value=Decimal("10.00"),
            notes="Updated draft",
            lines=[
                CreateOrderLineInput(
                    product_variant_id=replacement_variant.id,
                    quantity=3,
                ),
                CreateOrderLineInput(
                    product_variant_id=original_variant.id,
                    quantity=1,
                    unit_price=Decimal("5.00"),
                ),
            ],
        ),
    )

    assert updated_order.id == order.id
    assert updated_order.order_number == order.order_number
    assert updated_order.customer_id == replacement_customer.id
    assert updated_order.status == OrderStatus.CONFIRMED
    assert updated_order.order_date == date(2026, 4, 17)
    assert updated_order.deadline == date(2026, 5, 1)
    assert updated_order.notes == "Updated draft"
    assert updated_order.subtotal_amount == Decimal("80.00")
    assert updated_order.discount_type == DiscountType.FIXED
    assert updated_order.discount_value == Decimal("10.00")
    assert updated_order.discount_amount == Decimal("10.00")
    assert updated_order.total_amount == Decimal("70.00")
    assert len(updated_order.lines) == 2
    assert [line.product_variant_id for line in updated_order.lines] == [
        replacement_variant.id,
        original_variant.id,
    ]
    assert [line.quantity for line in updated_order.lines] == [3, 1]
    assert [line.line_total for line in updated_order.lines] == [
        Decimal("75.00"),
        Decimal("5.00"),
    ]


def test_update_order_service_rejects_terminal_order(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session)
    order = CreateOrderService(db_session).execute(
        CreateOrderInput(
            customer_id=customer.id,
            order_date=date(2026, 4, 16),
            lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=1)],
        )
    )
    order.status = OrderStatus.COMPLETED
    db_session.flush()

    with pytest.raises(ValueError, match="Only active orders can be edited."):
        UpdateOrderService(db_session).execute(
            order.id,
            UpdateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=2)],
            ),
        )


def test_create_order_service_rejects_missing_or_inactive_customer(db_session):
    inactive_customer = create_customer(db_session, is_active=False)
    variant = create_product_variant(db_session)

    with pytest.raises(ValueError, match="Customer not found."):
        CreateOrderService(db_session).execute(
            CreateOrderInput(
                customer_id=999999,
                order_date=date(2026, 4, 16),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=1)],
            )
        )

    with pytest.raises(ValueError, match="Customer must be active"):
        CreateOrderService(db_session).execute(
            CreateOrderInput(
                customer_id=inactive_customer.id,
                order_date=date(2026, 4, 16),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=1)],
            )
        )


def test_create_order_service_rejects_missing_or_inactive_variants(db_session):
    customer = create_customer(db_session)
    inactive_variant = create_product_variant(db_session, variant_is_active=False)

    with pytest.raises(ValueError, match="Line #1 product variant not found."):
        CreateOrderService(db_session).execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                lines=[CreateOrderLineInput(product_variant_id=999999, quantity=1)],
            )
        )

    with pytest.raises(ValueError, match="Line #1 product variant must be active."):
        CreateOrderService(db_session).execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                lines=[CreateOrderLineInput(product_variant_id=inactive_variant.id, quantity=1)],
            )
        )


def test_create_order_service_rejects_inactive_product(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session, product_is_active=False)

    with pytest.raises(ValueError, match="Line #1 product must be active."):
        CreateOrderService(db_session).execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=1)],
            )
        )


def test_create_order_service_rejects_invalid_lines_and_prices(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session, base_price=None)
    service = CreateOrderService(db_session)

    with pytest.raises(ValueError, match="An order must have at least one line."):
        service.execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
            )
        )

    with pytest.raises(ValueError, match="Line #1 quantity must be positive."):
        service.execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=0)],
            )
        )

    with pytest.raises(ValueError, match="Line #1 quantity cannot be greater than 999999."):
        service.execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                lines=[
                    CreateOrderLineInput(
                        product_variant_id=variant.id,
                        quantity=1000000,
                        unit_price=Decimal("0.00"),
                    )
                ],
            )
        )

    with pytest.raises(ValueError, match="Line #1 unit price cannot be negative."):
        service.execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                lines=[
                    CreateOrderLineInput(
                        product_variant_id=variant.id,
                        quantity=1,
                        unit_price=Decimal("-1.00"),
                    )
                ],
            )
        )

    with pytest.raises(ValueError, match="Line #1 unit price is required."):
        service.execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=1)],
            )
        )


def test_create_order_service_rejects_amounts_above_db_numeric_limit(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session)
    service = CreateOrderService(db_session)

    with pytest.raises(ValueError, match="Line #1 total cannot be greater"):
        service.execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                lines=[
                    CreateOrderLineInput(
                        product_variant_id=variant.id,
                        quantity=2,
                        unit_price=Decimal("50000000.00"),
                    )
                ],
            )
        )

    with pytest.raises(ValueError, match="Order subtotal cannot be greater"):
        service.execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                lines=[
                    CreateOrderLineInput(
                        product_variant_id=variant.id,
                        quantity=1,
                        unit_price=Decimal("50000000.00"),
                    ),
                    CreateOrderLineInput(
                        product_variant_id=variant.id,
                        quantity=1,
                        unit_price=Decimal("50000000.00"),
                    ),
                ],
            )
        )

    db_session.commit()

    assert db_session.query(Order).count() == 0


def test_create_order_service_rejects_invalid_discounts(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session)
    service = CreateOrderService(db_session)

    with pytest.raises(ValueError, match="Discount value cannot be negative."):
        service.execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                discount_type=DiscountType.FIXED,
                discount_value=Decimal("-1.00"),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=1)],
            )
        )

    with pytest.raises(ValueError, match="Discount value must be zero"):
        service.execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                discount_type=DiscountType.NONE,
                discount_value=Decimal("1.00"),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=1)],
            )
        )

    with pytest.raises(ValueError, match="Percentage discount cannot be greater than 100."):
        service.execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                discount_type=DiscountType.PERCENTAGE,
                discount_value=Decimal("100.01"),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=1)],
            )
        )

    with pytest.raises(ValueError, match="Fixed discount cannot be greater than the subtotal."):
        service.execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                discount_type=DiscountType.FIXED,
                discount_value=Decimal("999.00"),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=1)],
            )
        )


def test_create_order_service_rejects_deadline_before_order_date(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session)

    with pytest.raises(ValueError, match="Order deadline cannot be earlier"):
        CreateOrderService(db_session).execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                deadline=date(2026, 4, 15),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=1)],
            )
        )


def test_create_order_service_validation_failure_does_not_leave_pending_order(db_session):
    customer = create_customer(db_session)
    variant = create_product_variant(db_session)

    with pytest.raises(ValueError, match="Fixed discount cannot be greater than the subtotal."):
        CreateOrderService(db_session).execute(
            CreateOrderInput(
                customer_id=customer.id,
                order_date=date(2026, 4, 16),
                discount_type=DiscountType.FIXED,
                discount_value=Decimal("999.00"),
                lines=[CreateOrderLineInput(product_variant_id=variant.id, quantity=1)],
            )
        )

    db_session.commit()

    assert db_session.query(Order).count() == 0
