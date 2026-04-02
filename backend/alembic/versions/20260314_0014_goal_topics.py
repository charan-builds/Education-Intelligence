"""goal topics mapping

Revision ID: 20260314_0014
Revises: 20260313_0013
Create Date: 2026-03-14 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260314_0014"
down_revision: str | None = "20260313_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "goal_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("goal_id", "topic_id", name="uq_goal_topic"),
    )
    op.create_index(op.f("ix_goal_topics_id"), "goal_topics", ["id"], unique=False)
    op.create_index(op.f("ix_goal_topics_goal_id"), "goal_topics", ["goal_id"], unique=False)
    op.create_index(op.f("ix_goal_topics_topic_id"), "goal_topics", ["topic_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_goal_topics_topic_id"), table_name="goal_topics")
    op.drop_index(op.f("ix_goal_topics_goal_id"), table_name="goal_topics")
    op.drop_index(op.f("ix_goal_topics_id"), table_name="goal_topics")
    op.drop_table("goal_topics")
