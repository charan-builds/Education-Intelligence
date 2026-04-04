"""analytics snapshot index additions

Revision ID: 20260402_0020
Revises: 20260402_0019
Create Date: 2026-04-02 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0020"
down_revision = "20260402_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_analytics_snapshots_created_at_desc",
        "analytics_snapshots",
        [sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_analytics_snapshots_created_at_desc", table_name="analytics_snapshots")
