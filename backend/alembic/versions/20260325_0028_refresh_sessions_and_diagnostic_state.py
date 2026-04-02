"""refresh sessions and diagnostic answer identity

Revision ID: 20260325_0028
Revises: 20260325_0027
Create Date: 2026-03-25 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0028"
down_revision = "20260325_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"], unique=False)
    op.create_index("ix_refresh_sessions_expires_at", "refresh_sessions", ["expires_at"], unique=False)
    op.create_index("ix_refresh_sessions_revoked", "refresh_sessions", ["revoked"], unique=False)
    op.create_unique_constraint("uq_user_answers_test_question", "user_answers", ["test_id", "question_id"])


def downgrade() -> None:
    op.drop_constraint("uq_user_answers_test_question", "user_answers", type_="unique")
    op.drop_index("ix_refresh_sessions_revoked", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_expires_at", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_user_id", table_name="refresh_sessions")
    op.drop_table("refresh_sessions")
