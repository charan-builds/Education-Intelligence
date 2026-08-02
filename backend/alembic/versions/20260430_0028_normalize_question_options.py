"""normalize question options into a child table

Revision ID: 20260430_0028
Revises: 20260430_0027
Create Date: 2026-04-30 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260430_0028"
down_revision: Union[str, None] = "20260430_0027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "question_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("option_key", sa.String(length=8), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("position", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(trim(option_key)) > 0", name="ck_question_options_key_not_blank"),
        sa.CheckConstraint("length(trim(option_text)) > 0", name="ck_question_options_text_not_blank"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "option_key", name="uq_question_options_question_key"),
    )
    op.create_index(op.f("ix_question_options_id"), "question_options", ["id"], unique=False)
    op.create_index(op.f("ix_question_options_question_id"), "question_options", ["question_id"], unique=False)

    op.execute(
        """
        WITH expanded AS (
            SELECT
                q.id AS question_id,
                q.correct_answer,
                elem.value AS option_value,
                (elem.ordinality - 1)::integer AS position
            FROM questions q
            CROSS JOIN LATERAL jsonb_array_elements(COALESCE(q.options::jsonb, '[]'::jsonb))
                WITH ORDINALITY AS elem(value, ordinality)
        ),
        normalized AS (
            SELECT
                question_id,
                CASE
                    WHEN jsonb_typeof(option_value) = 'object'
                        THEN COALESCE(NULLIF(option_value->>'key', ''), NULLIF(option_value->>'option_key', ''))
                    ELSE NULL
                END AS provided_key,
                CASE
                    WHEN jsonb_typeof(option_value) = 'object'
                        THEN COALESCE(
                            NULLIF(option_value->>'text', ''),
                            NULLIF(option_value->>'option_text', ''),
                            NULLIF(option_value->>'label', ''),
                            NULLIF(option_value->>'value', ''),
                            option_value #>> '{}'
                        )
                    ELSE option_value #>> '{}'
                END AS option_text,
                CASE
                    WHEN jsonb_typeof(option_value) = 'object' AND option_value ? 'is_correct'
                        THEN COALESCE(NULLIF(option_value->>'is_correct', '')::boolean, false)
                    ELSE false
                END AS provided_is_correct,
                correct_answer,
                position
            FROM expanded
        )
        INSERT INTO question_options (
            question_id,
            option_key,
            option_text,
            is_correct,
            position,
            created_at,
            updated_at
        )
        SELECT
            question_id,
            COALESCE(
                NULLIF(trim(provided_key), ''),
                CASE WHEN position < 26 THEN chr(65 + position) ELSE (position + 1)::text END
            ) AS option_key,
            trim(option_text) AS option_text,
            provided_is_correct OR trim(option_text) = trim(correct_answer) AS is_correct,
            position,
            now(),
            now()
        FROM normalized
        WHERE trim(option_text) <> ''
        ON CONFLICT (question_id, option_key) DO NOTHING
        """
    )

    op.drop_column("questions", "options")


def downgrade() -> None:
    op.add_column("questions", sa.Column("options", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False))
    op.execute(
        """
        UPDATE questions q
        SET options = COALESCE(aggregated.options, '[]'::json)
        FROM (
            SELECT
                question_id,
                json_agg(
                    json_build_object(
                        'key', option_key,
                        'text', option_text,
                        'is_correct', is_correct
                    )
                    ORDER BY position, option_key
                ) AS options
            FROM question_options
            GROUP BY question_id
        ) AS aggregated
        WHERE aggregated.question_id = q.id
        """
    )
    op.drop_index(op.f("ix_question_options_question_id"), table_name="question_options")
    op.drop_index(op.f("ix_question_options_id"), table_name="question_options")
    op.drop_table("question_options")
