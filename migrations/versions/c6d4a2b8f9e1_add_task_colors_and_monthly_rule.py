"""add task colors and monthly rule

Revision ID: c6d4a2b8f9e1
Revises: e3b7c2a9d4f1
Create Date: 2026-05-11 23:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c6d4a2b8f9e1"
down_revision: str | None = "e3b7c2a9d4f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if not _has_column("task_series", "order_id"):
        op.add_column("task_series", sa.Column("order_id", sa.Integer(), nullable=True))
    if not _has_foreign_key("task_series", "fk_task_series_order_id_orders"):
        op.create_foreign_key(
            "fk_task_series_order_id_orders",
            "task_series",
            "orders",
            ["order_id"],
            ["id"],
            ondelete="CASCADE",
        )
    if not _has_column("task_series", "color_hex"):
        op.add_column(
            "task_series",
            sa.Column(
                "color_hex",
                sa.String(length=7),
                server_default="#2563eb",
                nullable=False,
            ),
        )
    if not _has_column("task_series", "monthly_rule"):
        op.add_column(
            "task_series",
            sa.Column(
                "monthly_rule",
                sa.String(length=32),
                server_default="DAY_OF_MONTH",
                nullable=False,
            ),
        )
    if not _has_column("task_series", "monthly_day"):
        op.add_column("task_series", sa.Column("monthly_day", sa.Integer(), nullable=True))
    if not _has_column("tasks", "color_hex"):
        op.add_column(
            "tasks",
            sa.Column(
                "color_hex",
                sa.String(length=7),
                server_default="#2563eb",
                nullable=False,
            ),
        )


def downgrade() -> None:
    if _has_column("tasks", "color_hex"):
        op.drop_column("tasks", "color_hex")
    if _has_column("task_series", "monthly_day"):
        op.drop_column("task_series", "monthly_day")
    if _has_column("task_series", "monthly_rule"):
        op.drop_column("task_series", "monthly_rule")
    if _has_column("task_series", "color_hex"):
        op.drop_column("task_series", "color_hex")
    if _has_foreign_key("task_series", "fk_task_series_order_id_orders"):
        op.drop_constraint("fk_task_series_order_id_orders", "task_series", type_="foreignkey")
    if _has_column("task_series", "order_id"):
        op.drop_column("task_series", "order_id")


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_foreign_key(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return constraint_name in {
        foreign_key["name"] for foreign_key in inspector.get_foreign_keys(table_name)
    }
