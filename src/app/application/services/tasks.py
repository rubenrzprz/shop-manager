from calendar import monthrange
from math import ceil
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.application.dto.tasks import (
    CalendarTaskDay,
    CreateTaskInput,
    CreateTaskSeriesInput,
    DEFAULT_TASK_COLOR_HEX,
    DashboardTaskList,
    TaskListItem,
    UpdateTaskInput,
)
from app.application.services.settings import ApplicationSettingsService
from app.domain.enums import (
    OrderStatus,
    TaskMonthlyRecurrenceRule,
    TaskRecurrenceType,
    TaskSeriesUpdateScope,
)
from app.infrastructure.db.models import Order, Task, TaskSeries

ACTIVE_ORDER_FOLLOW_UP_STATUSES = {
    OrderStatus.DRAFT,
    OrderStatus.CONFIRMED,
    OrderStatus.IN_PROGRESS,
    OrderStatus.READY,
}


class CreateTaskService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, data: CreateTaskInput) -> Task:
        self._validate_task_input(data)
        if data.order_id is not None and self._session.get(Order, data.order_id) is None:
            raise ValueError("Order not found.")

        task = Task(
            order_id=data.order_id,
            title=data.title.strip(),
            notes=data.notes,
            color_hex=_normalize_task_color(data.color_hex),
            due_date=data.due_date,
        )

        self._session.add(task)
        self._session.flush()

        return task

    @staticmethod
    def _validate_task_input(data: CreateTaskInput) -> None:
        if not data.title or not data.title.strip():
            raise ValueError("Task title is required.")
        _normalize_task_color(data.color_hex)


class GetTaskForEditService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, task_id: int) -> TaskListItem:
        task = self._session.get(
            Task,
            task_id,
            options=[joinedload(Task.order), joinedload(Task.series)],
        )
        if task is None:
            raise ValueError("Task not found.")

        return ListDashboardTasksService._to_list_item(task)


class DeleteTaskService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(
        self,
        task_id: int,
        scope: TaskSeriesUpdateScope = TaskSeriesUpdateScope.OCCURRENCE,
    ) -> None:
        task = self._session.get(Task, task_id, options=[joinedload(Task.series)])
        if task is None:
            raise ValueError("Task not found.")
        if task.is_auto_order_follow_up:
            raise ValueError("Automatic follow-up tasks cannot be deleted.")
        if scope != TaskSeriesUpdateScope.OCCURRENCE and task.series is None:
            raise ValueError("Task is not part of a recurring series.")
        if scope == TaskSeriesUpdateScope.SERIES:
            raise ValueError("Whole-series deletion is not supported.")

        if scope == TaskSeriesUpdateScope.OCCURRENCE:
            self._session.delete(task)
        else:
            self._delete_future_occurrences(task)
        self._session.flush()

    def _delete_future_occurrences(self, task: Task) -> None:
        tasks = self._session.scalars(
            select(Task)
            .where(Task.task_series_id == task.task_series_id)
            .where(Task.due_date >= task.due_date)
        ).all()
        for occurrence in tasks:
            self._session.delete(occurrence)


class UpdateTaskService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, task_id: int, data: UpdateTaskInput) -> Task:
        CreateTaskService._validate_task_input(
            CreateTaskInput(title=data.title, due_date=data.due_date, notes=data.notes)
        )
        task = self._session.get(Task, task_id, options=[joinedload(Task.series)])
        if task is None:
            raise ValueError("Task not found.")
        if task.is_auto_order_follow_up:
            raise ValueError("Automatic follow-up tasks cannot be edited.")
        if data.update_scope != TaskSeriesUpdateScope.OCCURRENCE and task.series is None:
            raise ValueError("Task is not part of a recurring series.")

        if data.update_scope == TaskSeriesUpdateScope.OCCURRENCE:
            self._apply_task_snapshot(task, data)
        elif data.update_scope == TaskSeriesUpdateScope.FUTURE:
            task = self._update_future_occurrences(task, data)
        else:
            task = self._update_whole_series(task, data)
        self._session.flush()
        return task

    def _apply_task_snapshot(self, task: Task, data: UpdateTaskInput) -> None:
        task.title = data.title.strip()
        task.notes = data.notes
        task.color_hex = _normalize_task_color(data.color_hex)
        task.due_date = data.due_date

    def _update_future_occurrences(self, task: Task, data: UpdateTaskInput) -> Task:
        series = task.series
        if series is None:
            raise ValueError("Task is not part of a recurring series.")
        recurrence_type = data.recurrence_type or series.recurrence_type
        interval = data.recurrence_interval or series.recurrence_interval
        self._validate_series_fields(
            title=data.title,
            recurrence_interval=interval,
            starts_on=data.due_date,
            ends_on=data.ends_on,
            monthly_rule=data.monthly_rule,
            monthly_day=data.monthly_day,
        )
        self._delete_incomplete_occurrences(series.id, task.due_date)
        series.title = data.title.strip()
        series.notes = data.notes
        series.color_hex = _normalize_task_color(data.color_hex)
        series.recurrence_type = recurrence_type
        series.recurrence_interval = interval
        series.monthly_rule = data.monthly_rule
        series.monthly_day = data.monthly_day
        series.starts_on = data.due_date
        series.ends_on = data.ends_on
        GenerateRecurringTasksService(self._session).execute(date.today())
        return self._first_generated_occurrence(series.id, max(date.today(), data.due_date))

    def _update_whole_series(self, task: Task, data: UpdateTaskInput) -> Task:
        series = task.series
        if series is None:
            raise ValueError("Task is not part of a recurring series.")
        recurrence_type = data.recurrence_type or series.recurrence_type
        interval = data.recurrence_interval or series.recurrence_interval
        self._validate_series_fields(
            title=data.title,
            recurrence_interval=interval,
            starts_on=data.due_date,
            ends_on=data.ends_on,
            monthly_rule=data.monthly_rule,
            monthly_day=data.monthly_day,
        )
        self._update_existing_occurrence_snapshots(series.id, data)
        self._delete_incomplete_occurrences(series.id, task.due_date)
        series.title = data.title.strip()
        series.notes = data.notes
        series.color_hex = _normalize_task_color(data.color_hex)
        series.recurrence_type = recurrence_type
        series.recurrence_interval = interval
        series.monthly_rule = data.monthly_rule
        series.monthly_day = data.monthly_day
        series.starts_on = data.due_date
        series.ends_on = data.ends_on
        GenerateRecurringTasksService(self._session).execute(date.today())
        return self._first_generated_occurrence(series.id, max(date.today(), data.due_date))

    def _update_existing_occurrence_snapshots(
        self,
        series_id: int,
        data: UpdateTaskInput,
    ) -> None:
        tasks = self._session.scalars(
            select(Task)
            .where(Task.task_series_id == series_id)
        ).all()
        for task in tasks:
            task.title = data.title.strip()
            task.notes = data.notes
            task.color_hex = _normalize_task_color(data.color_hex)

    def _delete_incomplete_occurrences(self, series_id: int, from_day: date) -> None:
        tasks = self._session.scalars(
            select(Task)
            .where(Task.task_series_id == series_id)
            .where(Task.completed_at.is_(None))
            .where(Task.due_date >= from_day)
        ).all()
        for task in tasks:
            self._session.delete(task)
        self._session.flush()

    def _first_generated_occurrence(self, series_id: int, from_day: date) -> Task:
        task = self._session.scalar(
            select(Task)
            .where(Task.task_series_id == series_id)
            .where(Task.due_date >= from_day)
            .order_by(Task.due_date, Task.id)
            .limit(1)
        )
        if task is None:
            raise ValueError("Recurring task update did not generate the selected occurrence.")
        return task

    @staticmethod
    def _validate_series_fields(
        *,
        title: str,
        recurrence_interval: int,
        starts_on: date,
        ends_on: date | None,
        monthly_rule: TaskMonthlyRecurrenceRule,
        monthly_day: int | None,
    ) -> None:
        CreateTaskSeriesService._validate_task_series_input(
            CreateTaskSeriesInput(
            title=title,
            recurrence_type=TaskRecurrenceType.DAILY,
                recurrence_interval=recurrence_interval,
                starts_on=starts_on,
                ends_on=ends_on,
                monthly_rule=monthly_rule,
                monthly_day=monthly_day,
            )
        )


class CreateTaskSeriesService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, data: CreateTaskSeriesInput) -> TaskSeries:
        self._validate_task_series_input(data)
        if data.order_id is not None and self._session.get(Order, data.order_id) is None:
            raise ValueError("Order not found.")

        series = TaskSeries(
            order_id=data.order_id,
            title=data.title.strip(),
            notes=data.notes,
            color_hex=_normalize_task_color(data.color_hex),
            recurrence_type=data.recurrence_type,
            recurrence_interval=data.recurrence_interval,
            monthly_rule=data.monthly_rule,
            monthly_day=data.monthly_day,
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
        if data.monthly_rule == TaskMonthlyRecurrenceRule.SPECIFIC_DAY_OF_MONTH:
            if data.monthly_day is None or not 1 <= data.monthly_day <= 31:
                raise ValueError("Task monthly day must be between 1 and 31.")
        _normalize_task_color(data.color_hex)


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
                        order_id=series.order_id,
                        title=series.title,
                        notes=series.notes,
                        color_hex=series.color_hex,
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
            .options(joinedload(Task.order), joinedload(Task.series))
            .where(Task.completed_at.is_(None))
            .where(Task.due_date < selected_day)
            .order_by(Task.due_date, Task.id)
        ).all()
        pending_today = self._session.scalars(
            select(Task)
            .options(joinedload(Task.order), joinedload(Task.series))
            .where(Task.completed_at.is_(None))
            .where(Task.due_date == selected_day)
            .order_by(Task.id)
        ).all()
        completed_today = self._session.scalars(
            select(Task)
            .options(joinedload(Task.order), joinedload(Task.series))
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
            order_id=task.order_id,
            order_number=task.order.order_number if task.order is not None else None,
            is_auto_order_follow_up=task.is_auto_order_follow_up,
            color_hex=task.color_hex,
            task_series_id=task.task_series_id,
            series_order_id=task.series.order_id if task.series is not None else None,
            recurrence_type=task.series.recurrence_type if task.series is not None else None,
            recurrence_interval=(
                task.series.recurrence_interval if task.series is not None else None
            ),
            monthly_rule=task.series.monthly_rule if task.series is not None else None,
            monthly_day=task.series.monthly_day if task.series is not None else None,
            series_starts_on=task.series.starts_on if task.series is not None else None,
            series_ends_on=task.series.ends_on if task.series is not None else None,
        )


class ListCalendarTasksService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, start_day: date, end_day: date) -> list[CalendarTaskDay]:
        if end_day < start_day:
            raise ValueError("Calendar end date cannot be before start date.")

        tasks = self._session.scalars(
            select(Task)
            .options(joinedload(Task.order), joinedload(Task.series))
            .where(Task.due_date >= start_day)
            .where(Task.due_date <= end_day)
            .order_by(Task.due_date, Task.completed_at.is_not(None), Task.id)
        ).all()
        tasks_by_day: dict[date, list[TaskListItem]] = {}
        for task in tasks:
            tasks_by_day.setdefault(task.due_date, []).append(
                ListDashboardTasksService._to_list_item(task)
            )

        return [
            CalendarTaskDay(day=day, tasks=tasks)
            for day, tasks in sorted(tasks_by_day.items())
        ]


class CompleteTaskService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, task_id: int, completed_at: datetime | None = None) -> Task:
        task = self._session.get(Task, task_id, options=[joinedload(Task.order)])
        if task is None:
            raise ValueError("Task not found.")

        if task.completed_at is None:
            task.completed_at = completed_at or datetime.now(timezone.utc)
            self._session.flush()
            if task.is_auto_order_follow_up:
                GenerateOrderFollowUpTasksService(self._session).schedule_next_for_task(task)

        return task


class ReopenTaskService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, task_id: int) -> Task:
        task = self._session.get(Task, task_id, options=[joinedload(Task.order)])
        if task is None:
            raise ValueError("Task not found.")

        if task.completed_at is not None and task.is_auto_order_follow_up:
            if (
                task.order is not None
                and task.order.status not in ACTIVE_ORDER_FOLLOW_UP_STATUSES
            ):
                raise ValueError("Automatic follow-ups cannot be reopened for inactive orders.")
            GenerateOrderFollowUpTasksService(self._session).delete_open_successor_for_task(task)
        task.completed_at = None
        self._session.flush()

        return task


class GenerateOrderFollowUpTasksService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, today: date | None = None) -> int:
        selected_day = today or date.today()
        orders = self._session.scalars(
            select(Order)
            .where(Order.status.in_(ACTIVE_ORDER_FOLLOW_UP_STATUSES))
            .order_by(Order.id)
        ).all()
        created_count = 0

        for order in orders:
            if self.ensure_open_follow_up_for_order(order, selected_day) is not None:
                created_count += 1

        self._session.flush()
        return created_count

    def ensure_open_follow_up_for_order(
        self,
        order: Order,
        today: date | None = None,
    ) -> Task | None:
        if order.status not in ACTIVE_ORDER_FOLLOW_UP_STATUSES:
            return None
        if self._has_open_follow_up(order.id):
            return None

        follow_up = self._new_follow_up_task(order, today or date.today())
        self._session.add(follow_up)
        self._session.flush()
        return follow_up

    def delete_open_follow_ups_for_order(self, order_id: int) -> None:
        open_follow_ups = self._session.scalars(
            select(Task)
            .where(Task.order_id == order_id)
            .where(Task.is_auto_order_follow_up.is_(True))
            .where(Task.completed_at.is_(None))
        ).all()
        for follow_up in open_follow_ups:
            self._session.delete(follow_up)
        self._session.flush()

    def recalculate_open_follow_ups(self, today: date | None = None) -> int:
        selected_day = today or date.today()
        orders = self._session.scalars(
            select(Order)
            .where(Order.status.in_(ACTIVE_ORDER_FOLLOW_UP_STATUSES))
            .order_by(Order.id)
        ).all()
        recalculated_count = 0
        for order in orders:
            self.delete_open_follow_ups_for_order(order.id)
            if self.ensure_open_follow_up_for_order(order, selected_day) is not None:
                recalculated_count += 1

        self._session.flush()
        return recalculated_count

    def schedule_next_for_task(self, task: Task) -> Task | None:
        if task.order_id is None:
            return None

        order = task.order or self._session.get(Order, task.order_id)
        if order is None or order.status not in ACTIVE_ORDER_FOLLOW_UP_STATUSES:
            return None
        if self._has_open_follow_up(order.id):
            return None

        follow_up_days = ApplicationSettingsService(
            self._session
        ).default_order_follow_up_days()
        completed_day = (task.completed_at or datetime.now(timezone.utc)).date()
        next_anchor_day = max(task.due_date, completed_day)
        next_task = self._new_follow_up_task(
            order,
            next_anchor_day,
            due_date=next_anchor_day + timedelta(days=follow_up_days),
        )
        self._session.add(next_task)
        self._session.flush()
        return next_task

    def delete_open_successor_for_task(self, task: Task) -> None:
        if task.order_id is None:
            return

        successor = self._session.scalar(
            select(Task)
            .where(Task.order_id == task.order_id)
            .where(Task.id != task.id)
            .where(Task.is_auto_order_follow_up.is_(True))
            .where(Task.completed_at.is_(None))
            .order_by(Task.due_date, Task.id)
            .limit(1)
        )
        if successor is not None:
            self._session.delete(successor)

    def _has_open_follow_up(self, order_id: int) -> bool:
        return (
            self._session.scalar(
                select(Task.id)
                .where(Task.order_id == order_id)
                .where(Task.is_auto_order_follow_up.is_(True))
                .where(Task.completed_at.is_(None))
                .limit(1)
            )
            is not None
        )

    def _new_follow_up_task(
        self,
        order: Order,
        today: date,
        *,
        due_date: date | None = None,
    ) -> Task:
        follow_up_days = ApplicationSettingsService(
            self._session
        ).default_order_follow_up_days()
        calculated_due_date = due_date or max(
            today,
            order.order_date + timedelta(days=follow_up_days),
        )
        return Task(
            order_id=order.id,
            is_auto_order_follow_up=True,
            title=f"Follow up {order.order_number}",
            notes="Automatic active-order follow-up reminder.",
            color_hex="#7c3aed",
            due_date=calculated_due_date,
        )


def _iter_occurrence_dates(
    series: TaskSeries,
    generation_start: date,
    generation_until: date,
) -> list[date]:
    occurrence_dates: list[date] = []
    occurrence_index = _first_occurrence_index(
        series.starts_on,
        series.recurrence_type,
        series.recurrence_interval,
        generation_start,
    )
    current_date = _next_occurrence_date(
        series.starts_on,
        series.recurrence_type,
        series.recurrence_interval,
        occurrence_index,
        getattr(series, "monthly_rule", TaskMonthlyRecurrenceRule.DAY_OF_MONTH),
        getattr(series, "monthly_day", None),
    )
    generation_end = min(
        generation_until,
        series.ends_on if series.ends_on is not None else generation_until,
    )
    while current_date <= generation_end:
        if current_date >= generation_start:
            occurrence_dates.append(current_date)
        current_date = _next_occurrence_date(
            series.starts_on,
            series.recurrence_type,
            series.recurrence_interval,
            occurrence_index + 1,
            getattr(series, "monthly_rule", TaskMonthlyRecurrenceRule.DAY_OF_MONTH),
            getattr(series, "monthly_day", None),
        )
        occurrence_index += 1

    return occurrence_dates


def _first_occurrence_index(
    starts_on: date,
    recurrence_type: TaskRecurrenceType,
    interval: int,
    generation_start: date,
) -> int:
    if generation_start <= starts_on:
        return 0

    if recurrence_type == TaskRecurrenceType.DAILY:
        return ceil((generation_start - starts_on).days / interval)
    if recurrence_type == TaskRecurrenceType.WEEKLY:
        return ceil((generation_start - starts_on).days / (interval * 7))
    if recurrence_type == TaskRecurrenceType.MONTHLY:
        month_delta = (generation_start.year - starts_on.year) * 12
        month_delta += generation_start.month - starts_on.month
        return max(0, month_delta // interval)

    raise ValueError("Task recurrence type is unsupported.")


def _next_occurrence_date(
    starts_on: date,
    recurrence_type: TaskRecurrenceType,
    interval: int,
    occurrence_index: int,
    monthly_rule: TaskMonthlyRecurrenceRule = TaskMonthlyRecurrenceRule.DAY_OF_MONTH,
    monthly_day: int | None = None,
) -> date:
    if recurrence_type == TaskRecurrenceType.DAILY:
        return starts_on + timedelta(days=interval * occurrence_index)
    if recurrence_type == TaskRecurrenceType.WEEKLY:
        return starts_on + timedelta(weeks=interval * occurrence_index)
    if recurrence_type == TaskRecurrenceType.MONTHLY:
        return _add_months(
            starts_on,
            interval * occurrence_index,
            monthly_rule=monthly_rule,
            monthly_day=monthly_day,
        )

    raise ValueError("Task recurrence type is unsupported.")


def _add_months(
    current_date: date,
    months: int,
    *,
    monthly_rule: TaskMonthlyRecurrenceRule = TaskMonthlyRecurrenceRule.DAY_OF_MONTH,
    monthly_day: int | None = None,
) -> date:
    month_index = current_date.month - 1 + months
    year = current_date.year + month_index // 12
    month = month_index % 12 + 1
    last_day = monthrange(year, month)[1]
    if monthly_rule == TaskMonthlyRecurrenceRule.FIRST_DAY_OF_MONTH:
        day = 1
    elif monthly_rule == TaskMonthlyRecurrenceRule.LAST_DAY_OF_MONTH:
        day = last_day
    elif monthly_rule == TaskMonthlyRecurrenceRule.SPECIFIC_DAY_OF_MONTH:
        day = min(monthly_day or current_date.day, last_day)
    else:
        day = min(current_date.day, last_day)
    return date(year, month, day)


def _normalize_task_color(color_hex: str | None) -> str:
    color = (color_hex or DEFAULT_TASK_COLOR_HEX).strip()
    if len(color) != 7 or not color.startswith("#"):
        raise ValueError("Task color must be a hex color.")
    try:
        int(color[1:], 16)
    except ValueError as exc:
        raise ValueError("Task color must be a hex color.") from exc
    return color.lower()
