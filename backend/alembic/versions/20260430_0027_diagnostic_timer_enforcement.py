"""add diagnostic timer enforcement fields

Revision ID: 20260430_0027
Revises: 20260430_0026
Create Date: 2026-04-30 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260430_0027"
down_revision: Union[str, None] = "20260430_0026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "diagnostic_tests",
        sa.Column("test_duration", sa.Integer(), server_default=sa.text("20"), nullable=True),
    )
    op.add_column("diagnostic_tests", sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE diagnostic_tests SET test_duration = COALESCE(test_duration, 20)")
    op.alter_column("diagnostic_tests", "test_duration", existing_type=sa.Integer(), nullable=False)
    op.create_check_constraint(
        "ck_diagnostic_tests_test_duration_positive",
        "diagnostic_tests",
        "test_duration > 0",
    )
    op.create_index(op.f("ix_diagnostic_tests_expired_at"), "diagnostic_tests", ["expired_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_diagnostic_tests_expired_at"), table_name="diagnostic_tests")
    op.drop_constraint("ck_diagnostic_tests_test_duration_positive", "diagnostic_tests", type_="check")
    op.drop_column("diagnostic_tests", "expired_at")
    op.drop_column("diagnostic_tests", "test_duration")
