from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.domain.enums import DiscountType, OrderStatus


@dataclass(frozen=True)
class CreateOrderLineInput:
    product_variant_id: int
    quantity: int
    unit_price: Decimal | None = None
    notes: str | None = None


@dataclass(frozen=True)
class CreateOrderInput:
    customer_id: int
    order_date: date
    deadline: date | None = None
    discount_type: DiscountType = DiscountType.NONE
    discount_value: Decimal = Decimal("0.00")
    notes: str | None = None
    lines: list[CreateOrderLineInput] = field(default_factory=list)


@dataclass(frozen=True)
class OrderLineListItem:
    id: int
    product_variant_id: int
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


@dataclass(frozen=True)
class OrderListItem:
    id: int
    order_number: str
    customer_id: int
    customer_name: str
    status: OrderStatus
    order_date: date
    deadline: date | None
    subtotal_amount: Decimal
    discount_type: DiscountType
    discount_value: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    lines: list[OrderLineListItem]
