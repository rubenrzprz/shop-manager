from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import TaskRecurrenceType
from app.infrastructure.db.session import Base


class TaskSeries(Base):
    __tablename__ = "task_series"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recurrence_type: Mapped[TaskRecurrenceType] = mapped_column(
        Enum(TaskRecurrenceType, name="task_recurrence_type_enum"),
        nullable=False,
    )
    recurrence_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    tasks = relationship("Task", back_populates="series")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("task_series_id", "due_date", name="uq_tasks_series_due_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_series_id: Mapped[int | None] = mapped_column(
        ForeignKey("task_series.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    series = relationship("TaskSeries", back_populates="tasks")
