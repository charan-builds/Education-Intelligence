"""add personal tenant type

Revision ID: 20260403_0021
Revises: 20260402_0020
Create Date: 2026-04-03 11:20:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260403_0021"
down_revision: str | Sequence[str] | None = "20260402_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE tenanttype ADD VALUE IF NOT EXISTS 'personal'")


def downgrade() -> None:
    # PostgreSQL enum value removal is intentionally left as a no-op.
    pass
