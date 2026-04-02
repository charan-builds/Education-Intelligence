"""postgres rls phase 2 tenant coverage

Revision ID: 20260402_0018
Revises: 20260402_0017
Create Date: 2026-04-02 02:30:00.000000
"""

from pathlib import Path

from alembic import op


revision = "20260402_0018"
down_revision = "20260402_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[2] / "sql" / "postgres_tenant_rls_phase2.sql"
    op.execute(sql_path.read_text(encoding="utf-8"))


def downgrade() -> None:
    # Intentional no-op downgrade. Removing RLS policies should be explicit and manual.
    pass
