from dataclasses import dataclass
from datetime import date, datetime

from app.domain.enums import TaskRecurrenceType


@dataclass(frozen=True)
class CreateTaskInput:
    title: str
    due_date: date
    notes: str | None = None
    order_id: int | None = None


@dataclass(frozen=True)
class UpdateTaskInput:
    title: str
    due_date: date
    notes: str | None = None


@dataclass(frozen=True)
class CreateTaskSeriesInput:
    title: str
    recurrence_type: TaskRecurrenceType
    starts_on: date
    recurrence_interval: int = 1
    notes: str | None = None
    ends_on: date | None = None


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


@dataclass(frozen=True)
class DashboardTaskList:
    overdue: list[TaskListItem]
    pending_today: list[TaskListItem]
    completed_today: list[TaskListItem]


@dataclass(frozen=True)
class CalendarTaskDay:
    day: date
    tasks: list[TaskListItem]
