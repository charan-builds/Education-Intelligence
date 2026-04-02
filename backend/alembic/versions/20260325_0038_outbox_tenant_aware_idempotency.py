"""outbox tenant-aware idempotency

Revision ID: 20260325_0038
Revises: 20260325_0037
Create Date: 2026-03-25 00:00:03.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0038"
down_revision = "20260325_0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_outbox_events_event_type_idempotency", "outbox_events", type_="unique")
    op.create_unique_constraint(
        "uq_outbox_events_tenant_event_idempotency",
        "outbox_events",
        ["tenant_id", "event_type", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_outbox_events_tenant_event_idempotency", "outbox_events", type_="unique")
    op.create_unique_constraint(
        "uq_outbox_events_event_type_idempotency",
        "outbox_events",
        ["event_type", "idempotency_key"],
    )
