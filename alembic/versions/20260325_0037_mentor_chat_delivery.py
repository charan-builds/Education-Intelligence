"""mentor chat delivery

Revision ID: 20260325_0037
Revises: 20260325_0036
Create Date: 2026-03-25 00:00:04.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0037"
down_revision = "20260325_0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mentor_chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("response_json", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", "request_id", "direction", name="uq_mentor_chat_request_direction"),
    )
    op.create_index("ix_mentor_chat_messages_id", "mentor_chat_messages", ["id"], unique=False)
    op.create_index("ix_mentor_chat_messages_tenant_id", "mentor_chat_messages", ["tenant_id"], unique=False)
    op.create_index("ix_mentor_chat_messages_user_id", "mentor_chat_messages", ["user_id"], unique=False)
    op.create_index("ix_mentor_chat_messages_request_id", "mentor_chat_messages", ["request_id"], unique=False)
    op.create_index("ix_mentor_chat_messages_direction", "mentor_chat_messages", ["direction"], unique=False)
    op.create_index("ix_mentor_chat_messages_status", "mentor_chat_messages", ["status"], unique=False)
    op.create_index("ix_mentor_chat_messages_created_at", "mentor_chat_messages", ["created_at"], unique=False)
    op.alter_column("mentor_chat_messages", "retry_count", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_mentor_chat_messages_created_at", table_name="mentor_chat_messages")
    op.drop_index("ix_mentor_chat_messages_status", table_name="mentor_chat_messages")
    op.drop_index("ix_mentor_chat_messages_direction", table_name="mentor_chat_messages")
    op.drop_index("ix_mentor_chat_messages_request_id", table_name="mentor_chat_messages")
    op.drop_index("ix_mentor_chat_messages_user_id", table_name="mentor_chat_messages")
    op.drop_index("ix_mentor_chat_messages_tenant_id", table_name="mentor_chat_messages")
    op.drop_index("ix_mentor_chat_messages_id", table_name="mentor_chat_messages")
    op.drop_table("mentor_chat_messages")
