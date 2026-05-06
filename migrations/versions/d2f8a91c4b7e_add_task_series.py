"""add task series

Revision ID: d2f8a91c4b7e
Revises: a7c9e2f4d6b1
Create Date: 2026-05-06 19:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d2f8a91c4b7e"
down_revision: str | None = "a7c9e2f4d6b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


task_recurrence_type_enum = sa.Enum(
    "DAILY",
    "WEEKLY",
    "MONTHLY",
    name="task_recurrence_type_enum",
)


def upgrade() -> None:
    op.create_table(
        "task_series",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recurrence_type", task_recurrence_type_enum, nullable=False),
        sa.Column("recurrence_interval", sa.Integer(), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("tasks", sa.Column("task_series_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_tasks_task_series_id_task_series",
        "tasks",
        "task_series",
        ["task_series_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_tasks_series_due_date",
        "tasks",
        ["task_series_id", "due_date"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_tasks_series_due_date", "tasks", type_="unique")
    op.drop_constraint("fk_tasks_task_series_id_task_series", "tasks", type_="foreignkey")
    op.drop_column("tasks", "task_series_id")
    op.drop_table("task_series")
    task_recurrence_type_enum.drop(op.get_bind(), checkfirst=True)
