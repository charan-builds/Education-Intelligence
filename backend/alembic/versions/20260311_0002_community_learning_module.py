"""community learning module

Revision ID: 20260311_0002
Revises: 20260310_0001
Create Date: 2026-03-11 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260311_0002"
down_revision: Union[str, None] = "20260310_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "communities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communities_id"), "communities", ["id"], unique=False)
    op.create_index(op.f("ix_communities_tenant_id"), "communities", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_communities_topic_id"), "communities", ["topic_id"], unique=False)

    op.create_table(
        "community_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["community_id"], ["communities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("community_id", "user_id", name="uq_community_member_user"),
    )
    op.create_index(op.f("ix_community_members_id"), "community_members", ["id"], unique=False)
    op.create_index(op.f("ix_community_members_tenant_id"), "community_members", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_community_members_community_id"), "community_members", ["community_id"], unique=False)
    op.create_index(op.f("ix_community_members_user_id"), "community_members", ["user_id"], unique=False)

    op.create_table(
        "discussion_threads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["community_id"], ["communities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_discussion_threads_id"), "discussion_threads", ["id"], unique=False)
    op.create_index(op.f("ix_discussion_threads_tenant_id"), "discussion_threads", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_discussion_threads_community_id"), "discussion_threads", ["community_id"], unique=False)
    op.create_index(op.f("ix_discussion_threads_author_user_id"), "discussion_threads", ["author_user_id"], unique=False)

    op.create_table(
        "badges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("awarded_for", sa.String(length=128), nullable=False),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_badges_id"), "badges", ["id"], unique=False)
    op.create_index(op.f("ix_badges_tenant_id"), "badges", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_badges_user_id"), "badges", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_badges_user_id"), table_name="badges")
    op.drop_index(op.f("ix_badges_tenant_id"), table_name="badges")
    op.drop_index(op.f("ix_badges_id"), table_name="badges")
    op.drop_table("badges")

    op.drop_index(op.f("ix_discussion_threads_author_user_id"), table_name="discussion_threads")
    op.drop_index(op.f("ix_discussion_threads_community_id"), table_name="discussion_threads")
    op.drop_index(op.f("ix_discussion_threads_tenant_id"), table_name="discussion_threads")
    op.drop_index(op.f("ix_discussion_threads_id"), table_name="discussion_threads")
    op.drop_table("discussion_threads")

    op.drop_index(op.f("ix_community_members_user_id"), table_name="community_members")
    op.drop_index(op.f("ix_community_members_community_id"), table_name="community_members")
    op.drop_index(op.f("ix_community_members_tenant_id"), table_name="community_members")
    op.drop_index(op.f("ix_community_members_id"), table_name="community_members")
    op.drop_table("community_members")

    op.drop_index(op.f("ix_communities_topic_id"), table_name="communities")
    op.drop_index(op.f("ix_communities_tenant_id"), table_name="communities")
    op.drop_index(op.f("ix_communities_id"), table_name="communities")
    op.drop_table("communities")
