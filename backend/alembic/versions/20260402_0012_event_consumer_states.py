"""event consumer states

Revision ID: 20260402_0012
Revises: 20260401_0011
Create Date: 2026-04-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0012"
down_revision = "20260401_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_consumer_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("consumer_name", sa.String(length=128), nullable=False),
        sa.Column("event_name", sa.String(length=128), nullable=False),
        sa.Column("message_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(length=512), nullable=True),
        sa.Column("first_received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("consumer_name", "message_id", name="uq_event_consumer_states_consumer_message"),
    )
    op.create_index("ix_event_consumer_states_tenant_id", "event_consumer_states", ["tenant_id"])
    op.create_index("ix_event_consumer_states_consumer_name", "event_consumer_states", ["consumer_name"])
    op.create_index("ix_event_consumer_states_event_name", "event_consumer_states", ["event_name"])
    op.create_index("ix_event_consumer_states_message_id", "event_consumer_states", ["message_id"])
    op.create_index("ix_event_consumer_states_status", "event_consumer_states", ["status"])
    op.create_index("ix_event_consumer_states_first_received_at", "event_consumer_states", ["first_received_at"])
    op.create_index("ix_event_consumer_states_last_processed_at", "event_consumer_states", ["last_processed_at"])


def downgrade() -> None:
    op.drop_index("ix_event_consumer_states_last_processed_at", table_name="event_consumer_states")
    op.drop_index("ix_event_consumer_states_first_received_at", table_name="event_consumer_states")
    op.drop_index("ix_event_consumer_states_status", table_name="event_consumer_states")
    op.drop_index("ix_event_consumer_states_message_id", table_name="event_consumer_states")
    op.drop_index("ix_event_consumer_states_event_name", table_name="event_consumer_states")
    op.drop_index("ix_event_consumer_states_consumer_name", table_name="event_consumer_states")
    op.drop_index("ix_event_consumer_states_tenant_id", table_name="event_consumer_states")
    op.drop_table("event_consumer_states")
