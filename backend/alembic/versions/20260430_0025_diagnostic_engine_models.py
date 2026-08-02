"""align diagnostic engine models

Revision ID: 20260430_0025
Revises: 20260404_0024
Create Date: 2026-04-30 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260430_0025"
down_revision: Union[str, None] = "20260404_0024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


question_difficulty = sa.Enum("easy", "medium", "hard", name="questiondifficulty")
question_type = sa.Enum("mcq", name="questiontype")


def upgrade() -> None:
    bind = op.get_bind()
    question_difficulty.create(bind, checkfirst=True)
    question_type.create(bind, checkfirst=True)

    op.alter_column(
        "questions",
        "difficulty",
        existing_type=sa.Integer(),
        type_=question_difficulty,
        postgresql_using=(
            "CASE difficulty::text "
            "WHEN '1' THEN 'easy'::questiondifficulty "
            "WHEN '2' THEN 'medium'::questiondifficulty "
            "WHEN '3' THEN 'hard'::questiondifficulty "
            "ELSE 'medium'::questiondifficulty END"
        ),
        nullable=False,
    )
    op.alter_column(
        "questions",
        "question_type",
        existing_type=sa.String(length=32),
        type_=question_type,
        postgresql_using="'mcq'::questiontype",
        nullable=False,
    )
    op.create_index(op.f("ix_questions_difficulty"), "questions", ["difficulty"], unique=False)
    op.add_column("questions", sa.Column("explanation", sa.Text(), nullable=True))
    op.alter_column("questions", "answer_options", new_column_name="options", existing_type=sa.JSON(), existing_nullable=False)
    op.add_column("questions", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("questions", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    for table_name in ("topics", "topic_prerequisites", "diagnostic_tests"):
        op.add_column(table_name, sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
        op.add_column(table_name, sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    op.alter_column("user_answers", "user_answer", new_column_name="selected_answer", existing_type=sa.Text(), existing_nullable=False)
    op.add_column("user_answers", sa.Column("is_correct", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.create_index(op.f("ix_user_answers_is_correct"), "user_answers", ["is_correct"], unique=False)
    op.add_column("user_answers", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("user_answers", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))


def downgrade() -> None:
    op.drop_column("user_answers", "updated_at")
    op.drop_column("user_answers", "created_at")
    op.drop_index(op.f("ix_user_answers_is_correct"), table_name="user_answers")
    op.drop_column("user_answers", "is_correct")
    op.alter_column("user_answers", "selected_answer", new_column_name="user_answer", existing_type=sa.Text(), existing_nullable=False)

    for table_name in ("diagnostic_tests", "topic_prerequisites", "topics"):
        op.drop_column(table_name, "updated_at")
        op.drop_column(table_name, "created_at")

    op.drop_column("questions", "updated_at")
    op.drop_column("questions", "created_at")
    op.alter_column("questions", "options", new_column_name="answer_options", existing_type=sa.JSON(), existing_nullable=False)
    op.drop_column("questions", "explanation")
    op.drop_index(op.f("ix_questions_difficulty"), table_name="questions")
    op.alter_column(
        "questions",
        "question_type",
        existing_type=question_type,
        type_=sa.String(length=32),
        postgresql_using="'multiple_choice'",
        nullable=False,
    )
    op.alter_column(
        "questions",
        "difficulty",
        existing_type=question_difficulty,
        type_=sa.Integer(),
        postgresql_using=(
            "CASE difficulty::text "
            "WHEN 'easy' THEN 1 "
            "WHEN 'medium' THEN 2 "
            "WHEN 'hard' THEN 3 "
            "ELSE 2 END"
        ),
        nullable=False,
    )

    bind = op.get_bind()
    question_type.drop(bind, checkfirst=True)
    question_difficulty.drop(bind, checkfirst=True)
