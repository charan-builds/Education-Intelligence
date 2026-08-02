"""add diagnostic test status tracking

Revision ID: 20260430_0029
Revises: 20260430_0028
Create Date: 2026-04-30 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260430_0029"
down_revision: Union[str, None] = "20260430_0028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "diagnostic_tests",
        sa.Column("status", sa.String(length=32), server_default="started", nullable=True),
    )
    op.execute(
        """
        UPDATE diagnostic_tests
        SET status = CASE
            WHEN expired_at IS NOT NULL THEN 'expired'
            WHEN completed_at IS NOT NULL THEN 'submitted'
            WHEN EXISTS (
                SELECT 1
                FROM diagnostic_test_states dts
                WHERE dts.test_id = diagnostic_tests.id
                  AND jsonb_array_length(COALESCE(dts.answered_question_ids, '[]'::jsonb)) > 0
            ) THEN 'in_progress'
            WHEN EXISTS (
                SELECT 1
                FROM user_answers ua
                WHERE ua.test_id = diagnostic_tests.id
            ) THEN 'in_progress'
            ELSE 'started'
        END
        """
    )
    op.execute("UPDATE diagnostic_tests SET status = COALESCE(status, 'started')")
    op.alter_column("diagnostic_tests", "status", existing_type=sa.String(length=32), nullable=False)
    op.create_check_constraint(
        "ck_diagnostic_tests_status",
        "diagnostic_tests",
        "status IN ('started', 'in_progress', 'submitted', 'expired', 'abandoned')",
    )
    op.create_index(op.f("ix_diagnostic_tests_status"), "diagnostic_tests", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_diagnostic_tests_status"), table_name="diagnostic_tests")
    op.drop_constraint("ck_diagnostic_tests_status", "diagnostic_tests", type_="check")
    op.drop_column("diagnostic_tests", "status")
