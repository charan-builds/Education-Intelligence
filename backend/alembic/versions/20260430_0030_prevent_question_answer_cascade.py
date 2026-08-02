"""prevent question deletes from cascading user answers

Revision ID: 20260430_0030
Revises: 20260430_0029
Create Date: 2026-04-30 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260430_0030"
down_revision: Union[str, None] = "20260430_0029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_FK_NAME = "fk_user_answers_question_id_questions_restrict"
DEFAULT_FK_NAME = "user_answers_question_id_fkey"


def _question_fk_name() -> str | None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for fk in inspector.get_foreign_keys("user_answers"):
        if fk.get("constrained_columns") == ["question_id"] and fk.get("referred_table") == "questions":
            return fk.get("name")
    return None


def _replace_question_fk(*, ondelete: str, name: str) -> None:
    existing_name = _question_fk_name()
    if existing_name:
        op.drop_constraint(existing_name, "user_answers", type_="foreignkey")
    op.create_foreign_key(
        name,
        "user_answers",
        "questions",
        ["question_id"],
        ["id"],
        ondelete=ondelete,
    )


def upgrade() -> None:
    _replace_question_fk(ondelete="RESTRICT", name=NEW_FK_NAME)


def downgrade() -> None:
    _replace_question_fk(ondelete="CASCADE", name=DEFAULT_FK_NAME)
