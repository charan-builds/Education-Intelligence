"""add answer options to questions

Revision ID: 20260313_0012
Revises: 20260313_0011
Create Date: 2026-03-13 00:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260313_0012"
down_revision: Union[str, None] = "20260313_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("answer_options", sa.JSON(), nullable=True),
    )
    op.execute("UPDATE questions SET answer_options = '[]' WHERE answer_options IS NULL")
    op.alter_column("questions", "answer_options", nullable=False)


def downgrade() -> None:
    op.drop_column("questions", "answer_options")
