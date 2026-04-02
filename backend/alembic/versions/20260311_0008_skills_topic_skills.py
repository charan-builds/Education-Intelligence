"""skills and topic_skills tables

Revision ID: 20260311_0008
Revises: 20260311_0007
Create Date: 2026-03-11 00:00:06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260311_0008"
down_revision: Union[str, None] = "20260311_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_skill_tenant_name"),
    )
    op.create_index(op.f("ix_skills_id"), "skills", ["id"], unique=False)
    op.create_index(op.f("ix_skills_tenant_id"), "skills", ["tenant_id"], unique=False)

    op.create_table(
        "topic_skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("topic_id", "skill_id", name="uq_topic_skill"),
    )
    op.create_index(op.f("ix_topic_skills_id"), "topic_skills", ["id"], unique=False)
    op.create_index(op.f("ix_topic_skills_topic_id"), "topic_skills", ["topic_id"], unique=False)
    op.create_index(op.f("ix_topic_skills_skill_id"), "topic_skills", ["skill_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_topic_skills_skill_id"), table_name="topic_skills")
    op.drop_index(op.f("ix_topic_skills_topic_id"), table_name="topic_skills")
    op.drop_index(op.f("ix_topic_skills_id"), table_name="topic_skills")
    op.drop_table("topic_skills")

    op.drop_index(op.f("ix_skills_tenant_id"), table_name="skills")
    op.drop_index(op.f("ix_skills_id"), table_name="skills")
    op.drop_table("skills")
