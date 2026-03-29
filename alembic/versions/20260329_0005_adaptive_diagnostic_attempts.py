"""adaptive diagnostic attempts

Revision ID: 20260329_0005
Revises: 20260328_0004
Create Date: 2026-03-29 00:05:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260329_0005"
down_revision: Union[str, None] = "20260328_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_answers",
        sa.Column("accuracy", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "user_answers",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("user_answers", "attempt_count")
    op.drop_column("user_answers", "accuracy")
