"""gamification foundation

Revision ID: 20260329_0007
Revises: 20260329_0006
Create Date: 2026-03-29 00:07:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260329_0007"
down_revision: Union[str, None] = "20260329_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gamification_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_level_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xp_to_next_level", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("current_streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("longest_streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_activity_on", sa.Date(), nullable=True),
        sa.Column("completed_topics_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_tests_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_gamification_profiles_tenant_user"),
    )
    op.create_index("ix_gamification_profiles_id", "gamification_profiles", ["id"])
    op.create_index("ix_gamification_profiles_tenant_id", "gamification_profiles", ["tenant_id"])
    op.create_index("ix_gamification_profiles_user_id", "gamification_profiles", ["user_id"])
    op.create_index("ix_gamification_profiles_last_activity_on", "gamification_profiles", ["last_activity_on"])

    op.create_table(
        "gamification_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("diagnostic_test_id", sa.Integer(), sa.ForeignKey("diagnostic_tests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("xp_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level_after", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("streak_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", "idempotency_key", name="uq_gamification_events_tenant_user_idempotency"),
    )
    op.create_index("ix_gamification_events_id", "gamification_events", ["id"])
    op.create_index("ix_gamification_events_tenant_id", "gamification_events", ["tenant_id"])
    op.create_index("ix_gamification_events_user_id", "gamification_events", ["user_id"])
    op.create_index("ix_gamification_events_event_type", "gamification_events", ["event_type"])
    op.create_index("ix_gamification_events_source_type", "gamification_events", ["source_type"])
    op.create_index("ix_gamification_events_source_id", "gamification_events", ["source_id"])
    op.create_index("ix_gamification_events_topic_id", "gamification_events", ["topic_id"])
    op.create_index("ix_gamification_events_diagnostic_test_id", "gamification_events", ["diagnostic_test_id"])
    op.create_index("ix_gamification_events_idempotency_key", "gamification_events", ["idempotency_key"])
    op.create_index("ix_gamification_events_awarded_at", "gamification_events", ["awarded_at"])

    connection = op.get_bind()
    users = connection.execute(
        sa.text("SELECT id, tenant_id, experience_points, current_streak_days, created_at FROM users")
    ).mappings()
    for user in users:
        total_xp = int(user["experience_points"] or 0)
        level = 1
        current_level_xp = total_xp
        xp_to_next_level = 200
        while current_level_xp >= xp_to_next_level:
            current_level_xp -= xp_to_next_level
            level += 1
            xp_to_next_level = 200 + (level - 1) * 50
        created_at = user["created_at"]
        connection.execute(
            sa.text(
                """
                INSERT INTO gamification_profiles (
                    tenant_id,
                    user_id,
                    level,
                    total_xp,
                    current_level_xp,
                    xp_to_next_level,
                    current_streak_days,
                    longest_streak_days,
                    last_activity_on,
                    completed_topics_count,
                    completed_tests_count,
                    created_at,
                    updated_at
                ) VALUES (
                    :tenant_id,
                    :user_id,
                    :level,
                    :total_xp,
                    :current_level_xp,
                    :xp_to_next_level,
                    :current_streak_days,
                    :longest_streak_days,
                    NULL,
                    0,
                    0,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "tenant_id": int(user["tenant_id"]),
                "user_id": int(user["id"]),
                "level": level,
                "total_xp": total_xp,
                "current_level_xp": current_level_xp,
                "xp_to_next_level": xp_to_next_level,
                "current_streak_days": int(user["current_streak_days"] or 0),
                "longest_streak_days": int(user["current_streak_days"] or 0),
                "created_at": created_at,
                "updated_at": created_at,
            },
        )


def downgrade() -> None:
    op.drop_index("ix_gamification_events_awarded_at", table_name="gamification_events")
    op.drop_index("ix_gamification_events_idempotency_key", table_name="gamification_events")
    op.drop_index("ix_gamification_events_diagnostic_test_id", table_name="gamification_events")
    op.drop_index("ix_gamification_events_topic_id", table_name="gamification_events")
    op.drop_index("ix_gamification_events_source_id", table_name="gamification_events")
    op.drop_index("ix_gamification_events_source_type", table_name="gamification_events")
    op.drop_index("ix_gamification_events_event_type", table_name="gamification_events")
    op.drop_index("ix_gamification_events_user_id", table_name="gamification_events")
    op.drop_index("ix_gamification_events_tenant_id", table_name="gamification_events")
    op.drop_index("ix_gamification_events_id", table_name="gamification_events")
    op.drop_table("gamification_events")

    op.drop_index("ix_gamification_profiles_last_activity_on", table_name="gamification_profiles")
    op.drop_index("ix_gamification_profiles_user_id", table_name="gamification_profiles")
    op.drop_index("ix_gamification_profiles_tenant_id", table_name="gamification_profiles")
    op.drop_index("ix_gamification_profiles_id", table_name="gamification_profiles")
    op.drop_table("gamification_profiles")
