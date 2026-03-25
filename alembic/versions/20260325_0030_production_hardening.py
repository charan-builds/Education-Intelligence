"""production hardening for idempotency, feature store, and notifications

Revision ID: 20260325_0030
Revises: 20260325_0029
Create Date: 2026-03-25 01:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0030"
down_revision = "20260325_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("learning_events", sa.Column("schema_version", sa.String(length=16), nullable=False, server_default="v1"))
    op.add_column("learning_events", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.create_index("ix_learning_events_idempotency_key", "learning_events", ["idempotency_key"], unique=False)
    op.create_unique_constraint(
        "uq_learning_events_tenant_user_idempotency",
        "learning_events",
        ["tenant_id", "user_id", "idempotency_key"],
    )

    op.drop_constraint("uq_user_skill_vectors_user_topic", "user_skill_vectors", type_="unique")
    op.create_unique_constraint(
        "uq_user_skill_vectors_tenant_user_topic",
        "user_skill_vectors",
        ["tenant_id", "user_id", "topic_id"],
    )

    op.add_column("notifications", sa.Column("priority", sa.String(length=16), nullable=False, server_default="normal"))
    op.add_column("notifications", sa.Column("dedupe_key", sa.String(length=128), nullable=True))
    op.add_column("notifications", sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_notifications_dedupe_key", "notifications", ["dedupe_key"], unique=False)
    op.create_index("ix_notifications_scheduled_for", "notifications", ["scheduled_for"], unique=False)
    op.create_unique_constraint(
        "uq_notifications_tenant_user_dedupe",
        "notifications",
        ["tenant_id", "user_id", "dedupe_key"],
    )

    op.create_table(
        "user_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("feature_set_name", sa.String(length=64), nullable=False, server_default="learner_features"),
        sa.Column("feature_values_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", "feature_set_name", name="uq_user_features_tenant_user_feature_set"),
    )
    op.create_index("ix_user_features_tenant_id", "user_features", ["tenant_id"], unique=False)
    op.create_index("ix_user_features_user_id", "user_features", ["user_id"], unique=False)
    op.create_index("ix_user_features_updated_at", "user_features", ["updated_at"], unique=False)

    op.create_table(
        "topic_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("feature_set_name", sa.String(length=64), nullable=False, server_default="topic_features"),
        sa.Column("feature_values_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "topic_id", "feature_set_name", name="uq_topic_features_tenant_topic_feature_set"),
    )
    op.create_index("ix_topic_features_tenant_id", "topic_features", ["tenant_id"], unique=False)
    op.create_index("ix_topic_features_topic_id", "topic_features", ["topic_id"], unique=False)
    op.create_index("ix_topic_features_updated_at", "topic_features", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_topic_features_updated_at", table_name="topic_features")
    op.drop_index("ix_topic_features_topic_id", table_name="topic_features")
    op.drop_index("ix_topic_features_tenant_id", table_name="topic_features")
    op.drop_table("topic_features")

    op.drop_index("ix_user_features_updated_at", table_name="user_features")
    op.drop_index("ix_user_features_user_id", table_name="user_features")
    op.drop_index("ix_user_features_tenant_id", table_name="user_features")
    op.drop_table("user_features")

    op.drop_constraint("uq_notifications_tenant_user_dedupe", "notifications", type_="unique")
    op.drop_index("ix_notifications_scheduled_for", table_name="notifications")
    op.drop_index("ix_notifications_dedupe_key", table_name="notifications")
    op.drop_column("notifications", "scheduled_for")
    op.drop_column("notifications", "dedupe_key")
    op.drop_column("notifications", "priority")

    op.drop_constraint("uq_user_skill_vectors_tenant_user_topic", "user_skill_vectors", type_="unique")
    op.create_unique_constraint("uq_user_skill_vectors_user_topic", "user_skill_vectors", ["user_id", "topic_id"])

    op.drop_constraint("uq_learning_events_tenant_user_idempotency", "learning_events", type_="unique")
    op.drop_index("ix_learning_events_idempotency_key", table_name="learning_events")
    op.drop_column("learning_events", "idempotency_key")
    op.drop_column("learning_events", "schema_version")
