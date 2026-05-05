from datetime import date, datetime, timedelta, timezone

import pytest

from app.application.dto.tasks import CreateTaskInput
from app.application.services.tasks import (
    CompleteTaskService,
    CreateTaskService,
    ListDashboardTasksService,
    ReopenTaskService,
)


def test_create_task_service_creates_one_off_task(db_session):
    task = CreateTaskService(db_session).execute(
        CreateTaskInput(
            title="Call supplier",
            notes="Ask about delivery",
            due_date=date(2026, 5, 5),
        )
    )

    assert task.id is not None
    assert task.title == "Call supplier"
    assert task.notes == "Ask about delivery"
    assert task.due_date == date(2026, 5, 5)
    assert task.completed_at is None


def test_create_task_service_rejects_blank_title(db_session):
    with pytest.raises(ValueError, match="Task title is required."):
        CreateTaskService(db_session).execute(
            CreateTaskInput(title="  ", due_date=date(2026, 5, 5))
        )


def test_dashboard_tasks_service_groups_overdue_pending_and_completed_today(db_session):
    today = date(2026, 5, 5)
    service = CreateTaskService(db_session)
    overdue = service.execute(
        CreateTaskInput(title="Overdue task", due_date=today - timedelta(days=1))
    )
    pending_today = service.execute(CreateTaskInput(title="Today task", due_date=today))
    future = service.execute(
        CreateTaskInput(title="Future task", due_date=today + timedelta(days=1))
    )
    completed_today = service.execute(CreateTaskInput(title="Done task", due_date=today))
    completed_yesterday = service.execute(
        CreateTaskInput(title="Old done task", due_date=today - timedelta(days=2))
    )
    CompleteTaskService(db_session).execute(completed_today.id)
    CompleteTaskService(db_session).execute(completed_yesterday.id)
    completed_today.completed_at = datetime(2026, 5, 5, 10, 0, tzinfo=timezone.utc)
    completed_yesterday.completed_at = datetime(2026, 5, 4, 10, 0, tzinfo=timezone.utc)
    db_session.flush()

    task_list = ListDashboardTasksService(db_session).execute(today)

    assert [task.id for task in task_list.overdue] == [overdue.id]
    assert [task.id for task in task_list.pending_today] == [pending_today.id]
    assert [task.id for task in task_list.completed_today] == [completed_today.id]
    assert future.id not in [task.id for task in task_list.overdue]


def test_complete_and_reopen_task_services_update_completion_state(db_session):
    task = CreateTaskService(db_session).execute(
        CreateTaskInput(title="Check order", due_date=date(2026, 5, 5))
    )

    CompleteTaskService(db_session).execute(task.id)

    assert task.completed_at is not None

    ReopenTaskService(db_session).execute(task.id)

    assert task.completed_at is None


def test_task_status_services_check_missing_task_before_update(db_session):
    with pytest.raises(ValueError, match="Task not found."):
        CompleteTaskService(db_session).execute(999)

    with pytest.raises(ValueError, match="Task not found."):
        ReopenTaskService(db_session).execute(999)
