"""spaced repetition topic scores

Revision ID: 20260329_0006
Revises: 20260329_0005
Create Date: 2026-03-29 00:06:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260329_0006"
down_revision: Union[str, None] = "20260329_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "topic_scores",
        sa.Column("revision_interval_days", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "topic_scores",
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE topic_scores SET revision_interval_days = review_interval_days")


def downgrade() -> None:
    op.drop_column("topic_scores", "last_seen")
    op.drop_column("topic_scores", "revision_interval_days")
