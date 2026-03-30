from datetime import date
from decimal import Decimal

from app.domain.enums import CustomerType, DiscountType, OrderStatus
from app.infrastructure.db.models import (
    Customer,
    Order,
    OrderLine,
    Product,
    ProductVariant,
    Supplier,
)


def test_can_persist_core_order_flow(db_session):
    customer = Customer(
        customer_type=CustomerType.INDIVIDUAL,
        name="María Rodríguez Pérez",
        phone="+34 600000001",
        email="maria@example.com",
        city="La Laguna",
        country="Spain",
    )

    supplier = Supplier(
        name="Costuras Atlántico",
        phone="+34 600000002",
        email="atelier@example.com",
        city="Santa Cruz de Tenerife",
        country="Spain",
    )

    product = Product(
        supplier=supplier,
        name="Traditional Shirt A",
        description="Handcrafted traditional Canarian shirt",
        base_price=Decimal("49.90"),
        track_stock=False,
    )

    variant = ProductVariant(
        product=product,
        sku="TEST-PRD-0001-V01",
        size="M",
        color="White",
        variant_name="Size M / White",
        description="Default smoke-test variant",
        price_override=None,
        stock_current=None,
        stock_minimum=None,
    )

    order = Order(
        order_number="TEST-ORD-000001",
        customer=customer,
        status=OrderStatus.DRAFT,
        order_date=date.today(),
        deadline=None,
        subtotal_amount=Decimal("49.90"),
        discount_type=DiscountType.NONE,
        discount_value=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("49.90"),
        notes="Initial integration smoke test",
    )

    order_line = OrderLine(
        order=order,
        product_variant=variant,
        quantity=1,
        unit_price=Decimal("49.90"),
        line_total=Decimal("49.90"),
        notes="Smoke test line",
    )

    db_session.add_all([
        customer,
        supplier,
        product,
        variant,
        order,
        order_line,
    ])
    db_session.flush()

    assert customer.id is not None
    assert supplier.id is not None
    assert product.id is not None
    assert variant.id is not None
    assert order.id is not None
    assert order_line.id is not None

    assert order.customer_id == customer.id
    assert order_line.order_id == order.id
    assert order_line.product_variant_id == variant.id