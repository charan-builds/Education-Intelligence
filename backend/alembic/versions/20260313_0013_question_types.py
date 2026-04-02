"""add question type to questions

Revision ID: 20260313_0013
Revises: 20260313_0012
Create Date: 2026-03-13 00:40:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260313_0013"
down_revision: Union[str, None] = "20260313_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("question_type", sa.String(length=32), nullable=True))
    op.execute(
        "UPDATE questions SET question_type = CASE "
        "WHEN json_array_length(answer_options) > 0 THEN 'multiple_choice' "
        "ELSE 'short_text' END "
        "WHERE question_type IS NULL"
    )
    op.alter_column("questions", "question_type", nullable=False)


def downgrade() -> None:
    op.drop_column("questions", "question_type")
