"""kafka event streaming offsets and idempotency

Revision ID: 20260325_0033
Revises: 20260325_0032
Create Date: 2026-03-25 06:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0033"
down_revision = "20260325_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stream_consumer_offsets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("consumer_group", sa.String(length=128), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("partition", sa.Integer(), nullable=False),
        sa.Column("offset", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("consumer_group", "topic", "partition", name="uq_stream_consumer_offsets_group_topic_partition"),
    )
    op.create_index("ix_stream_consumer_offsets_consumer_group", "stream_consumer_offsets", ["consumer_group"], unique=False)
    op.create_index("ix_stream_consumer_offsets_topic", "stream_consumer_offsets", ["topic"], unique=False)

    op.create_table(
        "processed_stream_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("consumer_group", sa.String(length=128), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("partition", sa.Integer(), nullable=False),
        sa.Column("offset", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(length=128), nullable=False),
        sa.Column("event_name", sa.String(length=128), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("consumer_group", "message_id", name="uq_processed_stream_events_group_message"),
    )
    op.create_index("ix_processed_stream_events_tenant_id", "processed_stream_events", ["tenant_id"], unique=False)
    op.create_index("ix_processed_stream_events_consumer_group", "processed_stream_events", ["consumer_group"], unique=False)
    op.create_index("ix_processed_stream_events_topic", "processed_stream_events", ["topic"], unique=False)
    op.create_index("ix_processed_stream_events_message_id", "processed_stream_events", ["message_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_processed_stream_events_message_id", table_name="processed_stream_events")
    op.drop_index("ix_processed_stream_events_topic", table_name="processed_stream_events")
    op.drop_index("ix_processed_stream_events_consumer_group", table_name="processed_stream_events")
    op.drop_index("ix_processed_stream_events_tenant_id", table_name="processed_stream_events")
    op.drop_table("processed_stream_events")
    op.drop_index("ix_stream_consumer_offsets_topic", table_name="stream_consumer_offsets")
    op.drop_index("ix_stream_consumer_offsets_consumer_group", table_name="stream_consumer_offsets")
    op.drop_table("stream_consumer_offsets")
