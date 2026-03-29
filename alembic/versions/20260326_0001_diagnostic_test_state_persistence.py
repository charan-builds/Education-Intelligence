"""diagnostic test state persistence

Revision ID: 20260326_0001
Revises: 20260325_0038
Create Date: 2026-03-26 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260326_0001"
down_revision = "20260325_0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "diagnostic_test_states",
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("answered_question_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("previous_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("expected_next_question_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["test_id"], ["diagnostic_tests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("test_id"),
        sa.UniqueConstraint("test_id", name="uq_diagnostic_test_states_test_id"),
    )
    op.create_index("ix_diagnostic_test_states_tenant_id", "diagnostic_test_states", ["tenant_id"], unique=False)
    op.create_index("ix_diagnostic_test_states_user_id", "diagnostic_test_states", ["user_id"], unique=False)
    op.create_index("ix_diagnostic_test_states_goal_id", "diagnostic_test_states", ["goal_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_diagnostic_test_states_goal_id", table_name="diagnostic_test_states")
    op.drop_index("ix_diagnostic_test_states_user_id", table_name="diagnostic_test_states")
    op.drop_index("ix_diagnostic_test_states_tenant_id", table_name="diagnostic_test_states")
    op.drop_table("diagnostic_test_states")

