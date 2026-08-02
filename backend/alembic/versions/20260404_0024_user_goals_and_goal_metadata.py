"""user goals and goal metadata

Revision ID: 20260404_0024
Revises: 20260404_0023
Create Date: 2026-04-04 01:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260404_0024"
down_revision: Union[str, None] = "20260404_0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("goals", sa.Column("skills_covered", sa.JSON(), nullable=True))
    op.add_column("goals", sa.Column("estimated_duration_weeks", sa.Integer(), nullable=True))
    op.add_column("goals", sa.Column("difficulty_tag", sa.String(length=32), nullable=True))
    op.add_column("goals", sa.Column("roadmap_preview", sa.Text(), nullable=True))

    op.create_table(
        "user_goals",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goal_id", sa.Integer(), sa.ForeignKey("goals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("user_id", "goal_id", name="pk_user_goals"),
    )
    op.create_index("ix_user_goals_user_id", "user_goals", ["user_id"], unique=False)
    op.create_index("ix_user_goals_goal_id", "user_goals", ["goal_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_goals_goal_id", table_name="user_goals")
    op.drop_index("ix_user_goals_user_id", table_name="user_goals")
    op.drop_table("user_goals")
    op.drop_column("goals", "roadmap_preview")
    op.drop_column("goals", "difficulty_tag")
    op.drop_column("goals", "estimated_duration_weeks")
    op.drop_column("goals", "skills_covered")
