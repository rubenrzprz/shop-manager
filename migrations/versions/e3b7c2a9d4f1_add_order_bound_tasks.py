"""add order bound tasks

Revision ID: e3b7c2a9d4f1
Revises: d2f8a91c4b7e
Create Date: 2026-05-11 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e3b7c2a9d4f1"
down_revision: str | None = "d2f8a91c4b7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("order_id", sa.Integer(), nullable=True))
    op.add_column(
        "tasks",
        sa.Column(
            "is_auto_order_follow_up",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_tasks_order_id_orders",
        "tasks",
        "orders",
        ["order_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_tasks_order_id_orders", "tasks", type_="foreignkey")
    op.drop_column("tasks", "is_auto_order_follow_up")
    op.drop_column("tasks", "order_id")
