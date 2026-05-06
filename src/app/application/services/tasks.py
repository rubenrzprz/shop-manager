from datetime import date, datetime, time, timedelta, timezone, tzinfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dto.tasks import CreateTaskInput, DashboardTaskList, TaskListItem
from app.infrastructure.db.models import Task


def _get_local_timezone() -> tzinfo:
    return datetime.now().astimezone().tzinfo or timezone.utc


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


class ListDashboardTasksService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, day: date | None = None) -> DashboardTaskList:
        selected_day = day or date.today()
        local_timezone = _get_local_timezone()
        completed_start = datetime.combine(selected_day, time.min, tzinfo=local_timezone)
        completed_end = datetime.combine(
            selected_day + timedelta(days=1),
            time.min,
            tzinfo=local_timezone,
        )
        completed_start_utc = completed_start.astimezone(timezone.utc)
        completed_end_utc = completed_end.astimezone(timezone.utc)

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
