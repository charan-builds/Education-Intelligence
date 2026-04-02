"""distributed realtime, dead letter queue, and analytics snapshots

Revision ID: 20260325_0031
Revises: 20260325_0030
Create Date: 2026-03-25 03:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0031"
down_revision = "20260325_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dead_letter_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("source_event_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("error_message", sa.String(length=512), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_event_id"], ["outbox_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dead_letter_events_tenant_id", "dead_letter_events", ["tenant_id"], unique=False)
    op.create_index("ix_dead_letter_events_source_event_id", "dead_letter_events", ["source_event_id"], unique=False)
    op.create_index("ix_dead_letter_events_source_type", "dead_letter_events", ["source_type"], unique=False)
    op.create_index("ix_dead_letter_events_event_type", "dead_letter_events", ["event_type"], unique=False)
    op.create_index("ix_dead_letter_events_created_at", "dead_letter_events", ["created_at"], unique=False)

    op.create_table(
        "analytics_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("snapshot_type", sa.String(length=64), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "snapshot_type",
            "subject_id",
            "window_start",
            "window_end",
            name="uq_analytics_snapshots_identity",
        ),
    )
    op.create_index("ix_analytics_snapshots_tenant_id", "analytics_snapshots", ["tenant_id"], unique=False)
    op.create_index("ix_analytics_snapshots_snapshot_type", "analytics_snapshots", ["snapshot_type"], unique=False)
    op.create_index("ix_analytics_snapshots_subject_id", "analytics_snapshots", ["subject_id"], unique=False)
    op.create_index("ix_analytics_snapshots_window_start", "analytics_snapshots", ["window_start"], unique=False)
    op.create_index("ix_analytics_snapshots_window_end", "analytics_snapshots", ["window_end"], unique=False)
    op.create_index("ix_analytics_snapshots_updated_at", "analytics_snapshots", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_analytics_snapshots_updated_at", table_name="analytics_snapshots")
    op.drop_index("ix_analytics_snapshots_window_end", table_name="analytics_snapshots")
    op.drop_index("ix_analytics_snapshots_window_start", table_name="analytics_snapshots")
    op.drop_index("ix_analytics_snapshots_subject_id", table_name="analytics_snapshots")
    op.drop_index("ix_analytics_snapshots_snapshot_type", table_name="analytics_snapshots")
    op.drop_index("ix_analytics_snapshots_tenant_id", table_name="analytics_snapshots")
    op.drop_table("analytics_snapshots")

    op.drop_index("ix_dead_letter_events_created_at", table_name="dead_letter_events")
    op.drop_index("ix_dead_letter_events_event_type", table_name="dead_letter_events")
    op.drop_index("ix_dead_letter_events_source_type", table_name="dead_letter_events")
    op.drop_index("ix_dead_letter_events_source_event_id", table_name="dead_letter_events")
    op.drop_index("ix_dead_letter_events_tenant_id", table_name="dead_letter_events")
    op.drop_table("dead_letter_events")
