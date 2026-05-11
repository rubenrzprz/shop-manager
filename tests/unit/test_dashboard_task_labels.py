from datetime import date, datetime
from decimal import Decimal

from app.application.dto.dashboard import DashboardOrderItem
from app.application.dto.tasks import TaskListItem
from app.domain.enums import OrderStatus
from app.ui.localization import set_language
from app.ui.widgets.dashboard_page import DashboardPage


def test_dashboard_task_label_does_not_translate_user_entered_notes():
    set_language("es")
    task = TaskListItem(
        id=1,
        title="Call customer",
        notes="Settings",
        due_date=date(2026, 5, 11),
        completed_at=None,
    )

    try:
        label = DashboardPage._task_label(task)
    finally:
        set_language("en")

    assert label == "2026-05-11 - Call customer (Settings)"


def test_dashboard_task_label_translates_system_auto_follow_up_notes():
    set_language("es")
    task = TaskListItem(
        id=1,
        title="Follow up ORD-000001",
        notes="Automatic active-order follow-up reminder.",
        due_date=date(2026, 5, 11),
        completed_at=None,
        order_id=1,
        order_number="ORD-000001",
        is_auto_order_follow_up=True,
    )

    try:
        label = DashboardPage._task_label(task)
    finally:
        set_language("en")

    assert label == (
        "2026-05-11 - [ORD-000001] Seguimiento "
        "(Recordatorio automático de seguimiento de pedido activo.)"
    )


def test_recent_order_activity_uses_full_timestamp_for_same_day_updates():
    order = DashboardOrderItem(
        id=1,
        order_number="ORD-000001",
        customer_name="Customer",
        status=OrderStatus.DRAFT,
        order_date=date(2026, 5, 11),
        deadline=None,
        total_amount=Decimal("10.00"),
        created_at=datetime(2026, 5, 11, 9, 0),
        updated_at=datetime(2026, 5, 11, 10, 0),
    )

    assert DashboardPage._recent_activity_label(order).startswith("Updated")
