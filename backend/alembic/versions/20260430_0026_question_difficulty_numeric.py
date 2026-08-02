"""replace question difficulty enum with numeric level and label

Revision ID: 20260430_0026
Revises: 20260430_0025
Create Date: 2026-04-30 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260430_0026"
down_revision: Union[str, None] = "20260430_0025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


question_difficulty = sa.Enum("easy", "medium", "hard", name="questiondifficulty")


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("difficulty_level", sa.Integer(), server_default=sa.text("2"), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("difficulty_label", sa.String(length=16), server_default=sa.text("'medium'"), nullable=True),
    )

    op.execute(
        """
        UPDATE questions
        SET
            difficulty_level = CASE difficulty::text
                WHEN 'easy' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'hard' THEN 3
                WHEN '1' THEN 1
                WHEN '2' THEN 2
                WHEN '3' THEN 3
                ELSE 2
            END,
            difficulty_label = CASE difficulty::text
                WHEN 'easy' THEN 'easy'
                WHEN 'medium' THEN 'medium'
                WHEN 'hard' THEN 'hard'
                WHEN '1' THEN 'easy'
                WHEN '2' THEN 'medium'
                WHEN '3' THEN 'hard'
                ELSE 'medium'
            END
        """
    )
    op.execute(
        """
        UPDATE questions
        SET
            version = COALESCE(version, 1),
            is_active = COALESCE(is_active, true)
        """
    )

    op.alter_column("questions", "version", existing_type=sa.Integer(), nullable=False)
    op.alter_column("questions", "is_active", existing_type=sa.Boolean(), nullable=False)
    op.alter_column("questions", "difficulty_level", existing_type=sa.Integer(), nullable=False)
    op.alter_column("questions", "difficulty_label", existing_type=sa.String(length=16), nullable=False)
    op.create_check_constraint(
        "ck_questions_version_positive",
        "questions",
        "version >= 1",
    )
    op.create_check_constraint(
        "ck_questions_difficulty_level",
        "questions",
        "difficulty_level BETWEEN 1 AND 3",
    )
    op.create_check_constraint(
        "ck_questions_difficulty_label",
        "questions",
        "difficulty_label IN ('easy', 'medium', 'hard')",
    )
    op.create_index(op.f("ix_questions_difficulty_level"), "questions", ["difficulty_level"], unique=False)
    op.create_index(op.f("ix_questions_difficulty_label"), "questions", ["difficulty_label"], unique=False)
    op.create_index(op.f("ix_questions_is_active"), "questions", ["is_active"], unique=False)

    op.drop_index(op.f("ix_questions_difficulty"), table_name="questions")
    op.drop_column("questions", "difficulty")
    question_difficulty.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    question_difficulty.create(op.get_bind(), checkfirst=True)
    op.add_column("questions", sa.Column("difficulty", question_difficulty, nullable=True))
    op.execute(
        """
        UPDATE questions
        SET difficulty = CASE
            WHEN difficulty_label = 'easy' OR difficulty_level = 1 THEN 'easy'::questiondifficulty
            WHEN difficulty_label = 'hard' OR difficulty_level = 3 THEN 'hard'::questiondifficulty
            ELSE 'medium'::questiondifficulty
        END
        """
    )
    op.alter_column("questions", "difficulty", existing_type=question_difficulty, nullable=False)
    op.create_index(op.f("ix_questions_difficulty"), "questions", ["difficulty"], unique=False)

    op.drop_index(op.f("ix_questions_is_active"), table_name="questions")
    op.drop_index(op.f("ix_questions_difficulty_label"), table_name="questions")
    op.drop_index(op.f("ix_questions_difficulty_level"), table_name="questions")
    op.drop_constraint("ck_questions_version_positive", "questions", type_="check")
    op.drop_constraint("ck_questions_difficulty_label", "questions", type_="check")
    op.drop_constraint("ck_questions_difficulty_level", "questions", type_="check")
    op.drop_column("questions", "difficulty_label")
    op.drop_column("questions", "difficulty_level")
    op.drop_column("questions", "is_active")
    op.drop_column("questions", "version")
