from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class CreateTaskInput:
    title: str
    due_date: date
    notes: str | None = None


@dataclass(frozen=True)
class TaskListItem:
    id: int
    title: str
    notes: str | None
    due_date: date
    completed_at: datetime | None


@dataclass(frozen=True)
class DashboardTaskList:
    overdue: list[TaskListItem]
    pending_today: list[TaskListItem]
    completed_today: list[TaskListItem]
