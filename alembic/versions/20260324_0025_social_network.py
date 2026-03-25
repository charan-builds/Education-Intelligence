"""social network

Revision ID: 20260324_0025
Revises: 20260324_0024
Create Date: 2026-03-24 00:25:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260324_0025"
down_revision = "20260324_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "social_follows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("follower_user_id", sa.Integer(), nullable=False),
        sa.Column("followed_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["followed_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["follower_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "follower_user_id", "followed_user_id", name="uq_social_follow_unique"),
    )
    op.create_index(op.f("ix_social_follows_id"), "social_follows", ["id"], unique=False)
    op.create_index(op.f("ix_social_follows_tenant_id"), "social_follows", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_social_follows_follower_user_id"), "social_follows", ["follower_user_id"], unique=False)
    op.create_index(op.f("ix_social_follows_followed_user_id"), "social_follows", ["followed_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_social_follows_followed_user_id"), table_name="social_follows")
    op.drop_index(op.f("ix_social_follows_follower_user_id"), table_name="social_follows")
    op.drop_index(op.f("ix_social_follows_tenant_id"), table_name="social_follows")
    op.drop_index(op.f("ix_social_follows_id"), table_name="social_follows")
    op.drop_table("social_follows")
