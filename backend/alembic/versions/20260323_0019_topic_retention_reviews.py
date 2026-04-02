"""topic retention review scheduling

Revision ID: 20260323_0019
Revises: 20260323_0018
Create Date: 2026-03-23 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260323_0019"
down_revision: str | Sequence[str] | None = "20260323_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("topic_scores", sa.Column("retention_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("topic_scores", sa.Column("review_interval_days", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("topic_scores", sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("topic_scores", "retention_score", server_default=None)
    op.alter_column("topic_scores", "review_interval_days", server_default=None)


def downgrade() -> None:
    op.drop_column("topic_scores", "review_due_at")
    op.drop_column("topic_scores", "review_interval_days")
    op.drop_column("topic_scores", "retention_score")
