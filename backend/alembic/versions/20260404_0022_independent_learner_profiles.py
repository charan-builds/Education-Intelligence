"""independent learner user profiles

Revision ID: 20260404_0022
Revises: 20260403_0021
Create Date: 2026-04-04 00:22:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260404_0022"
down_revision: Union[str, None] = "20260403_0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("profile_photo_url", sa.String(length=4096), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("college_name", sa.String(length=255), nullable=True),
        sa.Column("degree", sa.String(length=255), nullable=True),
        sa.Column("year_of_study", sa.Integer(), nullable=True),
        sa.Column("github_url", sa.String(length=2048), nullable=True),
        sa.Column("leetcode_url", sa.String(length=2048), nullable=True),
        sa.Column("hackerrank_url", sa.String(length=2048), nullable=True),
        sa.Column("linkedin_url", sa.String(length=2048), nullable=True),
        sa.Column("experience_level", sa.String(length=64), nullable=True),
        sa.Column("daily_study_time", sa.String(length=64), nullable=True),
        sa.Column("learning_style", sa.String(length=64), nullable=True),
        sa.Column("learning_goal_note", sa.Text(), nullable=True),
        sa.Column("target_timeline", sa.String(length=128), nullable=True),
        sa.Column("profile_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_user_profiles_profile_completed", "user_profiles", ["profile_completed"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_profiles_profile_completed", table_name="user_profiles")
    op.drop_table("user_profiles")
