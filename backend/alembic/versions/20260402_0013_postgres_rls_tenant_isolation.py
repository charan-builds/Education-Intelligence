"""postgres rls tenant isolation

Revision ID: 20260402_0013
Revises: 20260402_0012
Create Date: 2026-04-02 00:30:00.000000
"""

from pathlib import Path

from alembic import op


revision = "20260402_0013"
down_revision = "20260402_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[2] / "sql" / "postgres_tenant_rls.sql"
    op.execute(sql_path.read_text(encoding="utf-8"))


def downgrade() -> None:
    # Intentional no-op downgrade for RLS bootstrap. Policies may be removed explicitly if rollback is required.
    pass
