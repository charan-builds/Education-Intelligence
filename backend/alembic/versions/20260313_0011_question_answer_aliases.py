"""add accepted answers to questions

Revision ID: 20260313_0011
Revises: 20260313_0010
Create Date: 2026-03-13 00:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260313_0011"
down_revision: Union[str, None] = "20260313_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("accepted_answers", sa.JSON(), nullable=True),
    )
    op.execute("UPDATE questions SET accepted_answers = '[]' WHERE accepted_answers IS NULL")
    op.alter_column("questions", "accepted_answers", nullable=False)


def downgrade() -> None:
    op.drop_column("questions", "accepted_answers")
