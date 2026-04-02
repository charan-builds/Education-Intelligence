"""ai requests async queue

Revision ID: 20260402_0015
Revises: 20260402_0014
Create Date: 2026-04-02 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0015"
down_revision = "20260402_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("request_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.String(length=512), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "user_id", "request_id", name="uq_ai_requests_tenant_user_request"),
    )
    op.create_index("ix_ai_requests_tenant_id", "ai_requests", ["tenant_id"])
    op.create_index("ix_ai_requests_user_id", "ai_requests", ["user_id"])
    op.create_index("ix_ai_requests_request_id", "ai_requests", ["request_id"])
    op.create_index("ix_ai_requests_request_type", "ai_requests", ["request_type"])
    op.create_index("ix_ai_requests_status", "ai_requests", ["status"])
    op.create_index("ix_ai_requests_created_at", "ai_requests", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_requests_created_at", table_name="ai_requests")
    op.drop_index("ix_ai_requests_status", table_name="ai_requests")
    op.drop_index("ix_ai_requests_request_type", table_name="ai_requests")
    op.drop_index("ix_ai_requests_request_id", table_name="ai_requests")
    op.drop_index("ix_ai_requests_user_id", table_name="ai_requests")
    op.drop_index("ix_ai_requests_tenant_id", table_name="ai_requests")
    op.drop_table("ai_requests")
