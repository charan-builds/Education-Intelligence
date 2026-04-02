"""resources table

Revision ID: 20260311_0007
Revises: 20260311_0006
Create Date: 2026-03-11 00:00:05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260311_0007"
down_revision: Union[str, None] = "20260311_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=True),
        sa.Column("resource_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("goal_relevance", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resources_created_at"), "resources", ["created_at"], unique=False)
    op.create_index(op.f("ix_resources_difficulty"), "resources", ["difficulty"], unique=False)
    op.create_index(op.f("ix_resources_goal_id"), "resources", ["goal_id"], unique=False)
    op.create_index(op.f("ix_resources_goal_relevance"), "resources", ["goal_relevance"], unique=False)
    op.create_index(op.f("ix_resources_id"), "resources", ["id"], unique=False)
    op.create_index(op.f("ix_resources_resource_type"), "resources", ["resource_type"], unique=False)
    op.create_index(op.f("ix_resources_tenant_id"), "resources", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_resources_topic_id"), "resources", ["topic_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_resources_topic_id"), table_name="resources")
    op.drop_index(op.f("ix_resources_tenant_id"), table_name="resources")
    op.drop_index(op.f("ix_resources_resource_type"), table_name="resources")
    op.drop_index(op.f("ix_resources_id"), table_name="resources")
    op.drop_index(op.f("ix_resources_goal_relevance"), table_name="resources")
    op.drop_index(op.f("ix_resources_goal_id"), table_name="resources")
    op.drop_index(op.f("ix_resources_difficulty"), table_name="resources")
    op.drop_index(op.f("ix_resources_created_at"), table_name="resources")
    op.drop_table("resources")
