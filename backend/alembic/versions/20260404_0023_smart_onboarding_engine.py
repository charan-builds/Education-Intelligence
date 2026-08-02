"""smart onboarding engine models

Revision ID: 20260404_0023
Revises: 20260404_0022
Create Date: 2026-04-04 00:23:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260404_0023"
down_revision: Union[str, None] = "20260404_0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("github_repo_count", sa.Integer(), nullable=True))
    op.add_column("user_profiles", sa.Column("github_languages", sa.JSON(), nullable=True))
    op.add_column("user_profiles", sa.Column("github_activity_score", sa.Float(), nullable=True))

    op.create_table(
        "learning_profiles",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_type", sa.String(length=64), nullable=False, server_default="balanced"),
        sa.Column("learning_speed", sa.Float(), nullable=False, server_default="50"),
        sa.Column("difficulty_preference", sa.String(length=32), nullable=False, server_default="moderate"),
        sa.Column("recommendation_bias", sa.String(length=64), nullable=False, server_default="foundations_first"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "onboarding_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_name", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_onboarding_events_user_step", "onboarding_events", ["user_id", "step_name", "event_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_onboarding_events_user_step", table_name="onboarding_events")
    op.drop_table("onboarding_events")
    op.drop_table("learning_profiles")
    op.drop_column("user_profiles", "github_activity_score")
    op.drop_column("user_profiles", "github_languages")
    op.drop_column("user_profiles", "github_repo_count")
