"""add discussion replies

Revision ID: 20260316_0015
Revises: 20260314_0014
Create Date: 2026-03-16 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260316_0015"
down_revision: str | Sequence[str] | None = "20260314_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "discussion_replies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thread_id"], ["discussion_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_discussion_replies_id"), "discussion_replies", ["id"], unique=False)
    op.create_index(op.f("ix_discussion_replies_tenant_id"), "discussion_replies", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_discussion_replies_thread_id"), "discussion_replies", ["thread_id"], unique=False)
    op.create_index(
        op.f("ix_discussion_replies_author_user_id"), "discussion_replies", ["author_user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_discussion_replies_author_user_id"), table_name="discussion_replies")
    op.drop_index(op.f("ix_discussion_replies_thread_id"), table_name="discussion_replies")
    op.drop_index(op.f("ix_discussion_replies_tenant_id"), table_name="discussion_replies")
    op.drop_index(op.f("ix_discussion_replies_id"), table_name="discussion_replies")
    op.drop_table("discussion_replies")
