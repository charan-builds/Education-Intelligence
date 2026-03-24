"""add correct answer to questions

Revision ID: 20260313_0010
Revises: 20260312_0009
Create Date: 2026-03-13 00:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260313_0010"
down_revision: Union[str, None] = "20260312_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("correct_answer", sa.Text(), nullable=True))
    op.execute("UPDATE questions SET correct_answer = question_text WHERE correct_answer IS NULL")
    op.alter_column("questions", "correct_answer", nullable=False)


def downgrade() -> None:
    op.drop_column("questions", "correct_answer")
