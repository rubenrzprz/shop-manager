from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.application.dto.dashboard import DashboardOrderItem, DashboardSummary
from app.domain.enums import OrderStatus
from app.infrastructure.db.models.orders import Order

ACTIVE_DASHBOARD_ORDER_STATUSES = (
    OrderStatus.DRAFT,
    OrderStatus.CONFIRMED,
    OrderStatus.IN_PROGRESS,
    OrderStatus.READY,
)


class GetDashboardSummaryService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(
        self,
        *,
        due_soon_limit: int = 5,
        recent_limit: int = 5,
    ) -> DashboardSummary:
        active_counts = self._active_order_counts()
        due_soon_orders = self._due_soon_orders(due_soon_limit)
        recent_orders = self._recent_orders(recent_limit)

        return DashboardSummary(
            active_order_counts=active_counts,
            due_soon_orders=[self._to_order_item(order) for order in due_soon_orders],
            recent_orders=[self._to_order_item(order) for order in recent_orders],
        )

    def _active_order_counts(self) -> dict[OrderStatus, int]:
        rows = self._session.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.status.in_(ACTIVE_DASHBOARD_ORDER_STATUSES))
            .group_by(Order.status)
        ).all()
        counts = {status: 0 for status in ACTIVE_DASHBOARD_ORDER_STATUSES}
        counts.update({status: count for status, count in rows})
        return counts

    def _due_soon_orders(self, limit: int) -> list[Order]:
        return list(
            self._session.scalars(
                select(Order)
                .options(joinedload(Order.customer))
                .where(Order.status.in_(ACTIVE_DASHBOARD_ORDER_STATUSES))
                .where(Order.deadline.is_not(None))
                .order_by(Order.deadline.asc(), Order.id.asc())
                .limit(limit)
            ).all()
        )

    def _recent_orders(self, limit: int) -> list[Order]:
        return list(
            self._session.scalars(
                select(Order)
                .options(joinedload(Order.customer))
                .order_by(Order.updated_at.desc(), Order.id.desc())
                .limit(limit)
            ).all()
        )

    @staticmethod
    def _to_order_item(order: Order) -> DashboardOrderItem:
        return DashboardOrderItem(
            id=order.id,
            order_number=order.order_number,
            customer_name=order.customer.name,
            status=order.status,
            order_date=order.order_date,
            deadline=order.deadline,
            total_amount=order.total_amount,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
