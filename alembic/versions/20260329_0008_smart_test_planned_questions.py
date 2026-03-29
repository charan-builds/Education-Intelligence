"""smart test planned questions

Revision ID: 20260329_0008
Revises: 20260329_0007
Create Date: 2026-03-29 00:08:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260329_0008"
down_revision: Union[str, None] = "20260329_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "diagnostic_test_states",
        sa.Column(
            "planned_question_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("diagnostic_test_states", "planned_question_ids")
