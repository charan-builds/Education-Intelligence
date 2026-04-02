"""outbox event lifecycle tracking

Revision ID: 20260402_0016
Revises: 20260402_0015
Create Date: 2026-04-02 00:00:16.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0016"
down_revision = "20260402_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outbox_events", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE outbox_events SET status = 'queued' WHERE status = 'pending'")
    op.execute("UPDATE outbox_events SET status = 'queued' WHERE status = 'processing'")
    op.execute("UPDATE outbox_events SET processed_at = dispatched_at WHERE status = 'dispatched' AND dispatched_at IS NOT NULL")
    op.execute("UPDATE outbox_events SET status = 'processed' WHERE status = 'dispatched' AND processed_at IS NOT NULL")


def downgrade() -> None:
    op.execute("UPDATE outbox_events SET status = 'dispatched' WHERE status = 'processed'")
    op.execute("UPDATE outbox_events SET status = 'pending' WHERE status = 'queued'")
    op.drop_column("outbox_events", "processed_at")
