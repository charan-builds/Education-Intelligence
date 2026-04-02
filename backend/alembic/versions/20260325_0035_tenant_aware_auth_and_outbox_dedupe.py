"""tenant aware auth and outbox dedupe

Revision ID: 20260325_0035
Revises: 20260325_0034
Create Date: 2026-03-25 00:00:02.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0035"
down_revision = "20260325_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("subdomain", sa.String(length=63), nullable=True))
    op.create_index("ix_tenants_subdomain", "tenants", ["subdomain"], unique=True)
    op.execute(
        """
        UPDATE tenants
        SET subdomain = lower(
            regexp_replace(
                regexp_replace(name, '[^a-zA-Z0-9]+', '-', 'g'),
                '(^-+|-+$)',
                '',
                'g'
            )
        )
        WHERE subdomain IS NULL
        """
    )

    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.create_unique_constraint("uq_users_tenant_email", "users", ["tenant_id", "email"])

    op.add_column("outbox_events", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
    op.create_index("ix_outbox_events_idempotency_key", "outbox_events", ["idempotency_key"], unique=False)
    op.create_unique_constraint(
        "uq_outbox_events_event_type_idempotency",
        "outbox_events",
        ["event_type", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_outbox_events_event_type_idempotency", "outbox_events", type_="unique")
    op.drop_index("ix_outbox_events_idempotency_key", table_name="outbox_events")
    op.drop_column("outbox_events", "idempotency_key")

    op.drop_constraint("uq_users_tenant_email", "users", type_="unique")
    op.create_unique_constraint("users_email_key", "users", ["email"])
    op.drop_column("users", "email_verified_at")

    op.drop_index("ix_tenants_subdomain", table_name="tenants")
    op.drop_column("tenants", "subdomain")
