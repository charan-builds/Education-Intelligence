"""analytics snapshot latest/data compatibility columns

Revision ID: 20260402_0019
Revises: 20260402_0018
Create Date: 2026-04-02 00:00:19.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260402_0019"
down_revision = "20260402_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    json_type = postgresql.JSONB(astext_type=sa.Text()) if dialect == "postgresql" else sa.JSON()

    op.add_column("analytics_snapshots", sa.Column("data", json_type, nullable=True))
    op.add_column("analytics_snapshots", sa.Column("version", sa.Integer(), nullable=True))
    op.add_column(
        "analytics_snapshots",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "analytics_snapshots",
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    if dialect == "postgresql":
        op.execute("UPDATE analytics_snapshots SET data = payload_json::jsonb WHERE data IS NULL")
    else:
        op.execute("UPDATE analytics_snapshots SET data = payload_json WHERE data IS NULL")
    op.execute("UPDATE analytics_snapshots SET version = snapshot_version WHERE version IS NULL")
    op.execute("UPDATE analytics_snapshots SET created_at = updated_at WHERE created_at IS NULL")

    if dialect == "postgresql":
        op.execute(
            """
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY tenant_id, snapshot_type, subject_id
                        ORDER BY snapshot_version DESC, updated_at DESC
                    ) AS rank_number
                FROM analytics_snapshots
            )
            UPDATE analytics_snapshots AS snapshots
            SET is_latest = (ranked.rank_number = 1)
            FROM ranked
            WHERE snapshots.id = ranked.id
            """
        )
    else:
        op.execute("UPDATE analytics_snapshots SET is_latest = false")

    op.alter_column("analytics_snapshots", "version", nullable=False)
    op.alter_column("analytics_snapshots", "created_at", nullable=False)
    op.create_index(
        "ix_analytics_snapshots_tenant_snapshot_latest",
        "analytics_snapshots",
        ["tenant_id", "snapshot_type", "is_latest"],
        unique=False,
    )
    op.alter_column("analytics_snapshots", "is_latest", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_analytics_snapshots_tenant_snapshot_latest", table_name="analytics_snapshots")
    op.drop_column("analytics_snapshots", "is_latest")
    op.drop_column("analytics_snapshots", "created_at")
    op.drop_column("analytics_snapshots", "version")
    op.drop_column("analytics_snapshots", "data")
