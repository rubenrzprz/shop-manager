from calendar import monthrange
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dto.tasks import (
    CreateTaskInput,
    CreateTaskSeriesInput,
    DashboardTaskList,
    TaskListItem,
)
from app.application.services.settings import ApplicationSettingsService
from app.domain.enums import TaskRecurrenceType
from app.infrastructure.db.models import Task, TaskSeries


class CreateTaskService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, data: CreateTaskInput) -> Task:
        self._validate_task_input(data)

        task = Task(
            title=data.title.strip(),
            notes=data.notes,
            due_date=data.due_date,
        )

        self._session.add(task)
        self._session.flush()

        return task

    @staticmethod
    def _validate_task_input(data: CreateTaskInput) -> None:
        if not data.title or not data.title.strip():
            raise ValueError("Task title is required.")


class CreateTaskSeriesService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, data: CreateTaskSeriesInput) -> TaskSeries:
        self._validate_task_series_input(data)

        series = TaskSeries(
            title=data.title.strip(),
            notes=data.notes,
            recurrence_type=data.recurrence_type,
            recurrence_interval=data.recurrence_interval,
            starts_on=data.starts_on,
            ends_on=data.ends_on,
            is_active=True,
        )

        self._session.add(series)
        self._session.flush()

        return series

    @staticmethod
    def _validate_task_series_input(data: CreateTaskSeriesInput) -> None:
        if not data.title or not data.title.strip():
            raise ValueError("Task series title is required.")
        if data.recurrence_interval < 1:
            raise ValueError("Task recurrence interval must be at least 1.")
        if data.ends_on is not None and data.ends_on < data.starts_on:
            raise ValueError("Task series end date cannot be before the start date.")


class GenerateRecurringTasksService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, today: date | None = None) -> int:
        generation_start = today or date.today()
        horizon_days = ApplicationSettingsService(self._session).task_generation_horizon_days()
        generation_until = generation_start + timedelta(days=horizon_days)
        series_list = self._session.scalars(
            select(TaskSeries)
            .where(TaskSeries.is_active.is_(True))
            .where(TaskSeries.starts_on <= generation_until)
            .where((TaskSeries.ends_on.is_(None)) | (TaskSeries.ends_on >= generation_start))
            .order_by(TaskSeries.id)
        ).all()
        if not series_list:
            return 0

        existing_due_dates_by_series_id = self._existing_due_dates_by_series_id(
            series_list,
            generation_start,
            generation_until,
        )
        created_count = 0
        for series in series_list:
            existing_due_dates = existing_due_dates_by_series_id.get(series.id, set())
            for due_date in _iter_occurrence_dates(
                series,
                generation_start,
                generation_until,
            ):
                if due_date in existing_due_dates:
                    continue

                self._session.add(
                    Task(
                        task_series_id=series.id,
                        title=series.title,
                        notes=series.notes,
                        due_date=due_date,
                    )
                )
                existing_due_dates.add(due_date)
                created_count += 1

        self._session.flush()
        return created_count

    def _existing_due_dates_by_series_id(
        self,
        series_list: list[TaskSeries],
        generation_start: date,
        generation_until: date,
    ) -> dict[int, set[date]]:
        series_ids = [series.id for series in series_list]
        rows = self._session.execute(
            select(Task.task_series_id, Task.due_date)
            .where(Task.task_series_id.in_(series_ids))
            .where(Task.due_date >= generation_start)
            .where(Task.due_date <= generation_until)
        ).all()
        due_dates_by_series_id: dict[int, set[date]] = {}
        for series_id, due_date in rows:
            if series_id is None:
                continue
            due_dates_by_series_id.setdefault(series_id, set()).add(due_date)

        return due_dates_by_series_id


class ListDashboardTasksService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, day: date | None = None) -> DashboardTaskList:
        selected_day = day or date.today()
        completed_start_utc = datetime.combine(selected_day, time.min).astimezone(timezone.utc)
        completed_end_utc = datetime.combine(
            selected_day + timedelta(days=1),
            time.min,
        ).astimezone(timezone.utc)

        overdue = self._session.scalars(
            select(Task)
            .where(Task.completed_at.is_(None))
            .where(Task.due_date < selected_day)
            .order_by(Task.due_date, Task.id)
        ).all()
        pending_today = self._session.scalars(
            select(Task)
            .where(Task.completed_at.is_(None))
            .where(Task.due_date == selected_day)
            .order_by(Task.id)
        ).all()
        completed_today = self._session.scalars(
            select(Task)
            .where(Task.completed_at >= completed_start_utc)
            .where(Task.completed_at < completed_end_utc)
            .order_by(Task.completed_at.desc(), Task.id.desc())
        ).all()

        return DashboardTaskList(
            overdue=[self._to_list_item(task) for task in overdue],
            pending_today=[self._to_list_item(task) for task in pending_today],
            completed_today=[self._to_list_item(task) for task in completed_today],
        )

    @staticmethod
    def _to_list_item(task: Task) -> TaskListItem:
        return TaskListItem(
            id=task.id,
            title=task.title,
            notes=task.notes,
            due_date=task.due_date,
            completed_at=task.completed_at,
        )


class CompleteTaskService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, task_id: int) -> Task:
        task = self._session.get(Task, task_id)
        if task is None:
            raise ValueError("Task not found.")

        if task.completed_at is None:
            task.completed_at = datetime.now(timezone.utc)
            self._session.flush()

        return task


class ReopenTaskService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, task_id: int) -> Task:
        task = self._session.get(Task, task_id)
        if task is None:
            raise ValueError("Task not found.")

        task.completed_at = None
        self._session.flush()

        return task


def _iter_occurrence_dates(
    series: TaskSeries,
    generation_start: date,
    generation_until: date,
) -> list[date]:
    occurrence_dates: list[date] = []
    current_date = series.starts_on
    generation_end = min(
        generation_until,
        series.ends_on if series.ends_on is not None else generation_until,
    )
    while current_date <= generation_end:
        if current_date >= generation_start:
            occurrence_dates.append(current_date)
        current_date = _next_occurrence_date(
            current_date,
            series.recurrence_type,
            series.recurrence_interval,
        )

    return occurrence_dates


def _next_occurrence_date(
    current_date: date,
    recurrence_type: TaskRecurrenceType,
    interval: int,
) -> date:
    if recurrence_type == TaskRecurrenceType.DAILY:
        return current_date + timedelta(days=interval)
    if recurrence_type == TaskRecurrenceType.WEEKLY:
        return current_date + timedelta(weeks=interval)
    if recurrence_type == TaskRecurrenceType.MONTHLY:
        return _add_months(current_date, interval)

    raise ValueError("Task recurrence type is unsupported.")


def _add_months(current_date: date, months: int) -> date:
    month_index = current_date.month - 1 + months
    year = current_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(current_date.day, monthrange(year, month)[1])
    return date(year, month, day)
