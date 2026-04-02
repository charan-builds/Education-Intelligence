"""roadmap step enhancements

Revision ID: 20260311_0004
Revises: 20260311_0003
Create Date: 2026-03-11 00:00:02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260311_0004"
down_revision: Union[str, None] = "20260311_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "roadmap_steps",
        sa.Column("estimated_time_hours", sa.Float(), nullable=False, server_default="4.0"),
    )
    op.add_column(
        "roadmap_steps",
        sa.Column("difficulty", sa.String(length=32), nullable=False, server_default="medium"),
    )
    op.add_column(
        "roadmap_steps",
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("roadmap_steps", "priority")
    op.drop_column("roadmap_steps", "difficulty")
    op.drop_column("roadmap_steps", "estimated_time_hours")
