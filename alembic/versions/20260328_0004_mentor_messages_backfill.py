"""mentor messages backfill

Revision ID: 20260328_0004
Revises: 20260328_0003
Create Date: 2026-03-28 00:04:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260328_0004"
down_revision = "20260328_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if "mentor_messages" in existing_tables:
        return

    op.create_table(
        "mentor_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id", name="uq_mentor_messages_request_id"),
    )
    op.create_index("ix_mentor_messages_id", "mentor_messages", ["id"], unique=False)
    op.create_index("ix_mentor_messages_tenant_id", "mentor_messages", ["tenant_id"], unique=False)
    op.create_index("ix_mentor_messages_user_id", "mentor_messages", ["user_id"], unique=False)
    op.create_index("ix_mentor_messages_request_id", "mentor_messages", ["request_id"], unique=True)
    op.create_index("ix_mentor_messages_status", "mentor_messages", ["status"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if "mentor_messages" not in existing_tables:
        return

    op.drop_index("ix_mentor_messages_status", table_name="mentor_messages")
    op.drop_index("ix_mentor_messages_request_id", table_name="mentor_messages")
    op.drop_index("ix_mentor_messages_user_id", table_name="mentor_messages")
    op.drop_index("ix_mentor_messages_tenant_id", table_name="mentor_messages")
    op.drop_index("ix_mentor_messages_id", table_name="mentor_messages")
    op.drop_table("mentor_messages")
