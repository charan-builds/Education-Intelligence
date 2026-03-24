"""mentor memory profiles and session summaries

Revision ID: 20260324_0021
Revises: 20260324_0020
Create Date: 2026-03-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260324_0021"
down_revision = "20260324_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mentor_memory_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("learner_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("weak_topics_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("strong_topics_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("past_mistakes_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("improvement_signals_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("preferred_learning_style", sa.String(length=64), nullable=False, server_default="balanced"),
        sa.Column("learning_speed", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_session_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_mentor_memory_profile_tenant_user"),
    )
    op.create_index("ix_mentor_memory_profiles_id", "mentor_memory_profiles", ["id"], unique=False)
    op.create_index("ix_mentor_memory_profiles_tenant_id", "mentor_memory_profiles", ["tenant_id"], unique=False)
    op.create_index("ix_mentor_memory_profiles_user_id", "mentor_memory_profiles", ["user_id"], unique=False)

    op.create_table(
        "mentor_session_memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="mentor_chat"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("discussed_topics_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("mistakes_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("insights_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mentor_session_memories_id", "mentor_session_memories", ["id"], unique=False)
    op.create_index("ix_mentor_session_memories_tenant_id", "mentor_session_memories", ["tenant_id"], unique=False)
    op.create_index("ix_mentor_session_memories_user_id", "mentor_session_memories", ["user_id"], unique=False)
    op.create_index(
        "ix_mentor_session_memories_tenant_user_created",
        "mentor_session_memories",
        ["tenant_id", "user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_mentor_session_memories_tenant_user_created", table_name="mentor_session_memories")
    op.drop_index("ix_mentor_session_memories_user_id", table_name="mentor_session_memories")
    op.drop_index("ix_mentor_session_memories_tenant_id", table_name="mentor_session_memories")
    op.drop_index("ix_mentor_session_memories_id", table_name="mentor_session_memories")
    op.drop_table("mentor_session_memories")

    op.drop_index("ix_mentor_memory_profiles_user_id", table_name="mentor_memory_profiles")
    op.drop_index("ix_mentor_memory_profiles_tenant_id", table_name="mentor_memory_profiles")
    op.drop_index("ix_mentor_memory_profiles_id", table_name="mentor_memory_profiles")
    op.drop_table("mentor_memory_profiles")
