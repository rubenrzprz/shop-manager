from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.domain.enums import OrderStatus


@dataclass(frozen=True)
class DashboardOrderItem:
    id: int
    order_number: str
    customer_name: str
    status: OrderStatus
    order_date: date
    deadline: date | None
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DashboardSummary:
    active_order_counts: dict[OrderStatus, int]
    due_soon_orders: list[DashboardOrderItem]
    recent_orders: list[DashboardOrderItem]
