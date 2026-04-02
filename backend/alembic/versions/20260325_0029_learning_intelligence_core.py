"""learning intelligence core tables and event extensions

Revision ID: 20260325_0029
Revises: 20260325_0028
Create Date: 2026-03-25 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0029"
down_revision = "20260325_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_skill_vectors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("mastery_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "topic_id", name="uq_user_skill_vectors_user_topic"),
    )
    op.create_index("ix_user_skill_vectors_tenant_id", "user_skill_vectors", ["tenant_id"], unique=False)
    op.create_index("ix_user_skill_vectors_user_id", "user_skill_vectors", ["user_id"], unique=False)
    op.create_index("ix_user_skill_vectors_topic_id", "user_skill_vectors", ["topic_id"], unique=False)
    op.create_index("ix_user_skill_vectors_last_updated", "user_skill_vectors", ["last_updated"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("notification_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="info"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("action_url", sa.String(length=512), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_tenant_id", "notifications", ["tenant_id"], unique=False)
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"], unique=False)
    op.create_index("ix_notifications_notification_type", "notifications", ["notification_type"], unique=False)
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"], unique=False)
    op.create_index("ix_notifications_read_at", "notifications", ["read_at"], unique=False)

    op.add_column("learning_events", sa.Column("action_type", sa.String(length=64), nullable=True))
    op.add_column("learning_events", sa.Column("time_spent_seconds", sa.Integer(), nullable=True))
    op.add_column("learning_events", sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_learning_events_action_type", "learning_events", ["action_type"], unique=False)
    op.create_index("ix_learning_events_event_timestamp", "learning_events", ["event_timestamp"], unique=False)

    op.execute("UPDATE learning_events SET action_type = event_type WHERE action_type IS NULL")
    op.execute("UPDATE learning_events SET event_timestamp = created_at WHERE event_timestamp IS NULL")


def downgrade() -> None:
    op.drop_index("ix_learning_events_event_timestamp", table_name="learning_events")
    op.drop_index("ix_learning_events_action_type", table_name="learning_events")
    op.drop_column("learning_events", "event_timestamp")
    op.drop_column("learning_events", "time_spent_seconds")
    op.drop_column("learning_events", "action_type")

    op.drop_index("ix_notifications_read_at", table_name="notifications")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_notification_type", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_notifications_tenant_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_user_skill_vectors_last_updated", table_name="user_skill_vectors")
    op.drop_index("ix_user_skill_vectors_topic_id", table_name="user_skill_vectors")
    op.drop_index("ix_user_skill_vectors_user_id", table_name="user_skill_vectors")
    op.drop_index("ix_user_skill_vectors_tenant_id", table_name="user_skill_vectors")
    op.drop_table("user_skill_vectors")
