"""learning events table

Revision ID: 20260311_0005
Revises: 20260311_0004
Create Date: 2026-03-11 00:00:03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260311_0005"
down_revision: Union[str, None] = "20260311_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learning_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("diagnostic_test_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["diagnostic_test_id"], ["diagnostic_tests.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_events_id"), "learning_events", ["id"], unique=False)
    op.create_index(op.f("ix_learning_events_tenant_id"), "learning_events", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_learning_events_user_id"), "learning_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_learning_events_event_type"), "learning_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_learning_events_topic_id"), "learning_events", ["topic_id"], unique=False)
    op.create_index(
        op.f("ix_learning_events_diagnostic_test_id"),
        "learning_events",
        ["diagnostic_test_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_learning_events_diagnostic_test_id"), table_name="learning_events")
    op.drop_index(op.f("ix_learning_events_topic_id"), table_name="learning_events")
    op.drop_index(op.f("ix_learning_events_event_type"), table_name="learning_events")
    op.drop_index(op.f("ix_learning_events_user_id"), table_name="learning_events")
    op.drop_index(op.f("ix_learning_events_tenant_id"), table_name="learning_events")
    op.drop_index(op.f("ix_learning_events_id"), table_name="learning_events")
    op.drop_table("learning_events")
