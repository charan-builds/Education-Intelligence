"""analytics snapshot versioning

Revision ID: 20260402_0017
Revises: 20260402_0016
Create Date: 2026-04-02 00:00:17.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0017"
down_revision = "20260402_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "analytics_snapshots",
        sa.Column("snapshot_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.drop_constraint("uq_analytics_snapshots_identity", "analytics_snapshots", type_="unique")
    op.create_unique_constraint(
        "uq_analytics_snapshots_identity",
        "analytics_snapshots",
        ["tenant_id", "snapshot_type", "subject_id", "window_start", "window_end", "snapshot_version"],
    )
    op.create_index(
        "ix_analytics_snapshots_snapshot_version",
        "analytics_snapshots",
        ["snapshot_version"],
        unique=False,
    )
    op.alter_column("analytics_snapshots", "snapshot_version", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_analytics_snapshots_snapshot_version", table_name="analytics_snapshots")
    op.drop_constraint("uq_analytics_snapshots_identity", "analytics_snapshots", type_="unique")
    op.create_unique_constraint(
        "uq_analytics_snapshots_identity",
        "analytics_snapshots",
        ["tenant_id", "snapshot_type", "subject_id", "window_start", "window_end"],
    )
    op.drop_column("analytics_snapshots", "snapshot_version")
