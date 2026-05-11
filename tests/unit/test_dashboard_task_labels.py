from datetime import date

from app.application.dto.tasks import TaskListItem
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
