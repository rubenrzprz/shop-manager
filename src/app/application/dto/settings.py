from dataclasses import dataclass

from app.domain.enums import OrderStatus


@dataclass(frozen=True)
class ApplicationSettingsItem:
    strict_order_workflow_enabled: bool = False
    app_language: str = "en"
    task_generation_horizon_days: int = 90
    default_order_follow_up_days: int = 7
    enabled_order_statuses: tuple[OrderStatus, ...] = (
        OrderStatus.DRAFT,
        OrderStatus.CONFIRMED,
        OrderStatus.IN_PROGRESS,
        OrderStatus.READY,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    )
