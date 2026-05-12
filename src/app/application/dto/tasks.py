from dataclasses import dataclass
from datetime import date, datetime

from app.domain.enums import (
    TaskMonthlyRecurrenceRule,
    TaskRecurrenceType,
    TaskSeriesUpdateScope,
)

DEFAULT_TASK_COLOR_HEX = "#2563eb"


@dataclass(frozen=True)
class CreateTaskInput:
    title: str
    due_date: date
    notes: str | None = None
    order_id: int | None = None
    color_hex: str = DEFAULT_TASK_COLOR_HEX


@dataclass(frozen=True)
class UpdateTaskInput:
    title: str
    due_date: date
    notes: str | None = None
    color_hex: str = DEFAULT_TASK_COLOR_HEX
    update_scope: TaskSeriesUpdateScope = TaskSeriesUpdateScope.OCCURRENCE
    recurrence_type: TaskRecurrenceType | None = None
    recurrence_interval: int | None = None
    monthly_rule: TaskMonthlyRecurrenceRule = TaskMonthlyRecurrenceRule.DAY_OF_MONTH
    monthly_day: int | None = None
    ends_on: date | None = None


@dataclass(frozen=True)
class CreateTaskSeriesInput:
    title: str
    recurrence_type: TaskRecurrenceType
    starts_on: date
    recurrence_interval: int = 1
    notes: str | None = None
    ends_on: date | None = None
    color_hex: str = DEFAULT_TASK_COLOR_HEX
    monthly_rule: TaskMonthlyRecurrenceRule = TaskMonthlyRecurrenceRule.DAY_OF_MONTH
    monthly_day: int | None = None
    order_id: int | None = None


@dataclass(frozen=True)
class TaskListItem:
    id: int
    title: str
    notes: str | None
    due_date: date
    completed_at: datetime | None
    order_id: int | None = None
    order_number: str | None = None
    is_auto_order_follow_up: bool = False
    color_hex: str = DEFAULT_TASK_COLOR_HEX
    task_series_id: int | None = None
    series_order_id: int | None = None
    recurrence_type: TaskRecurrenceType | None = None
    recurrence_interval: int | None = None
    monthly_rule: TaskMonthlyRecurrenceRule | None = None
    monthly_day: int | None = None
    series_starts_on: date | None = None
    series_ends_on: date | None = None


@dataclass(frozen=True)
class DashboardTaskList:
    overdue: list[TaskListItem]
    pending_today: list[TaskListItem]
    completed_today: list[TaskListItem]


@dataclass(frozen=True)
class CalendarTaskDay:
    day: date
    tasks: list[TaskListItem]
