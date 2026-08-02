"""add optimized question sampling index

Revision ID: 20260430_0031
Revises: 20260430_0030
Create Date: 2026-04-30 00:00:00
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect


revision: str = "20260430_0031"
down_revision: Union[str, None] = "20260430_0030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEX_NAME = "ix_questions_topic_difficulty_level_active_id"


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if _index_exists("questions", INDEX_NAME):
        return
    op.create_index(
        INDEX_NAME,
        "questions",
        ["topic_id", "difficulty_level", "is_active", "id"],
        unique=False,
    )


def downgrade() -> None:
    if not _index_exists("questions", INDEX_NAME):
        return
    op.drop_index(INDEX_NAME, table_name="questions")
