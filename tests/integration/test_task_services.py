import os
import time as time_module
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.application.dto.tasks import CreateTaskInput, CreateTaskSeriesInput
from app.application.services.settings import ApplicationSettingsService
from app.application.services.tasks import (
    CompleteTaskService,
    CreateTaskService,
    CreateTaskSeriesService,
    GenerateRecurringTasksService,
    ListDashboardTasksService,
    ReopenTaskService,
)
from app.domain.enums import TaskRecurrenceType
from app.infrastructure.db.models import Task


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


def test_create_task_series_service_creates_recurring_series(db_session):
    series = CreateTaskSeriesService(db_session).execute(
        CreateTaskSeriesInput(
            title="Water plants",
            notes="Back room",
            recurrence_type=TaskRecurrenceType.WEEKLY,
            recurrence_interval=2,
            starts_on=date(2026, 5, 5),
            ends_on=date(2026, 6, 5),
        )
    )

    assert series.id is not None
    assert series.title == "Water plants"
    assert series.notes == "Back room"
    assert series.recurrence_type == TaskRecurrenceType.WEEKLY
    assert series.recurrence_interval == 2
    assert series.starts_on == date(2026, 5, 5)
    assert series.ends_on == date(2026, 6, 5)
    assert series.is_active


def test_create_task_series_service_validates_input(db_session):
    service = CreateTaskSeriesService(db_session)

    with pytest.raises(ValueError, match="Task series title is required."):
        service.execute(
            CreateTaskSeriesInput(
                title=" ",
                recurrence_type=TaskRecurrenceType.DAILY,
                starts_on=date(2026, 5, 5),
            )
        )

    with pytest.raises(ValueError, match="Task recurrence interval must be at least 1."):
        service.execute(
            CreateTaskSeriesInput(
                title="Open store",
                recurrence_type=TaskRecurrenceType.DAILY,
                recurrence_interval=0,
                starts_on=date(2026, 5, 5),
            )
        )

    with pytest.raises(
        ValueError,
        match="Task series end date cannot be before the start date.",
    ):
        service.execute(
            CreateTaskSeriesInput(
                title="Open store",
                recurrence_type=TaskRecurrenceType.DAILY,
                starts_on=date(2026, 5, 5),
                ends_on=date(2026, 5, 4),
            )
        )


def test_generate_recurring_tasks_service_creates_missing_occurrences(db_session):
    series = CreateTaskSeriesService(db_session).execute(
        CreateTaskSeriesInput(
            title="Check displays",
            notes="Front window",
            recurrence_type=TaskRecurrenceType.DAILY,
            starts_on=date(2026, 5, 5),
            ends_on=date(2026, 5, 7),
        )
    )

    created_count = GenerateRecurringTasksService(db_session).execute(date(2026, 5, 5))

    tasks = db_session.scalars(
        select(Task).where(Task.task_series_id == series.id).order_by(Task.due_date)
    ).all()
    assert created_count == 3
    assert [task.due_date for task in tasks] == [
        date(2026, 5, 5),
        date(2026, 5, 6),
        date(2026, 5, 7),
    ]
    assert all(task.title == "Check displays" for task in tasks)
    assert all(task.notes == "Front window" for task in tasks)


def test_generate_recurring_tasks_service_is_idempotent(db_session):
    CreateTaskSeriesService(db_session).execute(
        CreateTaskSeriesInput(
            title="Count cash drawer",
            recurrence_type=TaskRecurrenceType.WEEKLY,
            starts_on=date(2026, 5, 5),
            ends_on=date(2026, 5, 19),
        )
    )
    service = GenerateRecurringTasksService(db_session)

    first_count = service.execute(date(2026, 5, 5))
    second_count = service.execute(date(2026, 5, 5))

    assert first_count == 3
    assert second_count == 0


def test_generate_recurring_tasks_service_respects_horizon_and_inactive_series(
    db_session,
):
    ApplicationSettingsService(db_session).set_task_generation_horizon_days(30)
    active_series = CreateTaskSeriesService(db_session).execute(
        CreateTaskSeriesInput(
            title="Monthly review",
            recurrence_type=TaskRecurrenceType.MONTHLY,
            starts_on=date(2026, 5, 5),
        )
    )
    inactive_series = CreateTaskSeriesService(db_session).execute(
        CreateTaskSeriesInput(
            title="Inactive reminder",
            recurrence_type=TaskRecurrenceType.DAILY,
            starts_on=date(2026, 5, 5),
        )
    )
    inactive_series.is_active = False
    db_session.flush()

    created_count = GenerateRecurringTasksService(db_session).execute(date(2026, 5, 5))

    tasks = db_session.scalars(
        select(Task).where(Task.task_series_id == active_series.id).order_by(Task.due_date)
    ).all()
    inactive_tasks = db_session.scalars(
        select(Task).where(Task.task_series_id == inactive_series.id)
    ).all()
    assert created_count == 1
    assert [task.due_date for task in tasks] == [date(2026, 5, 5)]
    assert inactive_tasks == []


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


def test_dashboard_tasks_service_uses_local_day_for_completed_tasks(
    db_session,
):
    if not hasattr(time_module, "tzset"):
        pytest.skip("time.tzset is required to force a local timezone for this test.")

    previous_timezone = os.environ.get("TZ")
    os.environ["TZ"] = "Europe/Madrid"
    time_module.tzset()
    selected_day = date(2026, 1, 5)
    service = CreateTaskService(db_session)
    early_local_day = service.execute(
        CreateTaskInput(title="Early local day", due_date=selected_day)
    )
    late_local_day = service.execute(CreateTaskInput(title="Late local day", due_date=selected_day))
    next_local_day = service.execute(CreateTaskInput(title="Next local day", due_date=selected_day))
    previous_local_day = service.execute(
        CreateTaskInput(title="Previous local day", due_date=selected_day)
    )
    early_local_day.completed_at = datetime(2026, 1, 4, 23, 30, tzinfo=timezone.utc)
    late_local_day.completed_at = datetime(2026, 1, 5, 22, 30, tzinfo=timezone.utc)
    next_local_day.completed_at = datetime(2026, 1, 5, 23, 0, tzinfo=timezone.utc)
    previous_local_day.completed_at = datetime(2026, 1, 4, 22, 30, tzinfo=timezone.utc)
    db_session.flush()

    try:
        task_list = ListDashboardTasksService(db_session).execute(selected_day)
    finally:
        if previous_timezone is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous_timezone
        time_module.tzset()

    assert [task.id for task in task_list.completed_today] == [
        late_local_day.id,
        early_local_day.id,
    ]


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
