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

from app.domain.enums import TaskMonthlyRecurrenceRule, TaskRecurrenceType
from app.infrastructure.db.session import Base


class TaskSeries(Base):
    __tablename__ = "task_series"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    color_hex: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#2563eb",
        server_default="#2563eb",
    )
    recurrence_type: Mapped[TaskRecurrenceType] = mapped_column(
        Enum(TaskRecurrenceType, name="task_recurrence_type_enum"),
        nullable=False,
    )
    recurrence_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    monthly_rule: Mapped[TaskMonthlyRecurrenceRule] = mapped_column(
        String(32),
        nullable=False,
        default=TaskMonthlyRecurrenceRule.DAY_OF_MONTH,
        server_default=TaskMonthlyRecurrenceRule.DAY_OF_MONTH,
    )
    monthly_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
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
    order = relationship("Order")


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
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    is_auto_order_follow_up: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    color_hex: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#2563eb",
        server_default="#2563eb",
    )
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
    order = relationship("Order", back_populates="tasks")
