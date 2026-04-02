"""learning intelligence production upgrade

Revision ID: 20260323_0018
Revises: 20260318_0017
Create Date: 2026-03-23 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260323_0018"
down_revision: str | Sequence[str] | None = "20260318_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("experience_points", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("current_streak_days", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("focus_score", sa.Float(), nullable=False, server_default="0"))

    op.add_column("roadmap_steps", sa.Column("step_type", sa.String(length=32), nullable=False, server_default="core"))
    op.add_column("roadmap_steps", sa.Column("rationale", sa.Text(), nullable=True))
    op.add_column("roadmap_steps", sa.Column("unlocks_topic_id", sa.Integer(), nullable=True))
    op.add_column("roadmap_steps", sa.Column("is_revision", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index(op.f("ix_roadmap_steps_unlocks_topic_id"), "roadmap_steps", ["unlocks_topic_id"], unique=False)
    op.create_foreign_key(
        "fk_roadmap_steps_unlocks_topic_id_topics",
        "roadmap_steps",
        "topics",
        ["unlocks_topic_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "topic_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("diagnostic_test_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("mastery_delta", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["diagnostic_test_id"], ["diagnostic_tests.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "topic_id", name="uq_topic_scores_user_topic"),
    )
    op.create_index(op.f("ix_topic_scores_id"), "topic_scores", ["id"], unique=False)
    op.create_index(op.f("ix_topic_scores_tenant_id"), "topic_scores", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_topic_scores_user_id"), "topic_scores", ["user_id"], unique=False)
    op.create_index(op.f("ix_topic_scores_topic_id"), "topic_scores", ["topic_id"], unique=False)
    op.create_index(op.f("ix_topic_scores_diagnostic_test_id"), "topic_scores", ["diagnostic_test_id"], unique=False)

    op.create_table(
        "mentor_suggestions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("suggestion_type", sa.String(length=64), nullable=False, server_default="focus"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("why_reason", sa.Text(), nullable=False),
        sa.Column("is_ai_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mentor_suggestions_id"), "mentor_suggestions", ["id"], unique=False)
    op.create_index(op.f("ix_mentor_suggestions_tenant_id"), "mentor_suggestions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_mentor_suggestions_user_id"), "mentor_suggestions", ["user_id"], unique=False)
    op.create_index(op.f("ix_mentor_suggestions_topic_id"), "mentor_suggestions", ["topic_id"], unique=False)

    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("success_metric", sa.String(length=128), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_experiments_id"), "experiments", ["id"], unique=False)
    op.create_index(op.f("ix_experiments_tenant_id"), "experiments", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_experiments_key"), "experiments", ["key"], unique=False)

    op.create_table(
        "experiment_variants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("population_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conversion_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("engagement_lift", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_experiment_variants_id"), "experiment_variants", ["id"], unique=False)
    op.create_index(op.f("ix_experiment_variants_experiment_id"), "experiment_variants", ["experiment_id"], unique=False)

    op.add_column("discussion_threads", sa.Column("upvotes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("discussion_threads", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("discussion_threads", sa.Column("best_answer_reply_id", sa.Integer(), nullable=True))
    op.add_column("discussion_threads", sa.Column("is_ai_assisted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_foreign_key(
        "fk_discussion_threads_best_answer_reply_id",
        "discussion_threads",
        "discussion_replies",
        ["best_answer_reply_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("discussion_replies", sa.Column("upvotes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("discussion_replies", sa.Column("is_best_answer", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("discussion_replies", sa.Column("is_ai_assisted", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.alter_column("users", "experience_points", server_default=None)
    op.alter_column("users", "current_streak_days", server_default=None)
    op.alter_column("users", "focus_score", server_default=None)
    op.alter_column("roadmap_steps", "step_type", server_default=None)
    op.alter_column("roadmap_steps", "is_revision", server_default=None)
    op.alter_column("topic_scores", "mastery_delta", server_default=None)
    op.alter_column("topic_scores", "confidence", server_default=None)
    op.alter_column("mentor_suggestions", "suggestion_type", server_default=None)
    op.alter_column("mentor_suggestions", "is_ai_generated", server_default=None)
    op.alter_column("experiments", "status", server_default=None)
    op.alter_column("experiments", "is_archived", server_default=None)
    op.alter_column("experiment_variants", "config_json", server_default=None)
    op.alter_column("experiment_variants", "population_size", server_default=None)
    op.alter_column("experiment_variants", "conversion_rate", server_default=None)
    op.alter_column("experiment_variants", "engagement_lift", server_default=None)
    op.alter_column("discussion_threads", "upvotes", server_default=None)
    op.alter_column("discussion_threads", "is_ai_assisted", server_default=None)
    op.alter_column("discussion_replies", "upvotes", server_default=None)
    op.alter_column("discussion_replies", "is_best_answer", server_default=None)
    op.alter_column("discussion_replies", "is_ai_assisted", server_default=None)


def downgrade() -> None:
    op.drop_column("discussion_replies", "is_ai_assisted")
    op.drop_column("discussion_replies", "is_best_answer")
    op.drop_column("discussion_replies", "upvotes")

    op.drop_constraint("fk_discussion_threads_best_answer_reply_id", "discussion_threads", type_="foreignkey")
    op.drop_column("discussion_threads", "is_ai_assisted")
    op.drop_column("discussion_threads", "best_answer_reply_id")
    op.drop_column("discussion_threads", "ai_summary")
    op.drop_column("discussion_threads", "upvotes")

    op.drop_index(op.f("ix_experiment_variants_experiment_id"), table_name="experiment_variants")
    op.drop_index(op.f("ix_experiment_variants_id"), table_name="experiment_variants")
    op.drop_table("experiment_variants")

    op.drop_index(op.f("ix_experiments_key"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_tenant_id"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_id"), table_name="experiments")
    op.drop_table("experiments")

    op.drop_index(op.f("ix_mentor_suggestions_topic_id"), table_name="mentor_suggestions")
    op.drop_index(op.f("ix_mentor_suggestions_user_id"), table_name="mentor_suggestions")
    op.drop_index(op.f("ix_mentor_suggestions_tenant_id"), table_name="mentor_suggestions")
    op.drop_index(op.f("ix_mentor_suggestions_id"), table_name="mentor_suggestions")
    op.drop_table("mentor_suggestions")

    op.drop_index(op.f("ix_topic_scores_diagnostic_test_id"), table_name="topic_scores")
    op.drop_index(op.f("ix_topic_scores_topic_id"), table_name="topic_scores")
    op.drop_index(op.f("ix_topic_scores_user_id"), table_name="topic_scores")
    op.drop_index(op.f("ix_topic_scores_tenant_id"), table_name="topic_scores")
    op.drop_index(op.f("ix_topic_scores_id"), table_name="topic_scores")
    op.drop_table("topic_scores")

    op.drop_constraint("fk_roadmap_steps_unlocks_topic_id_topics", "roadmap_steps", type_="foreignkey")
    op.drop_index(op.f("ix_roadmap_steps_unlocks_topic_id"), table_name="roadmap_steps")
    op.drop_column("roadmap_steps", "is_revision")
    op.drop_column("roadmap_steps", "unlocks_topic_id")
    op.drop_column("roadmap_steps", "rationale")
    op.drop_column("roadmap_steps", "step_type")

    op.drop_column("users", "focus_score")
    op.drop_column("users", "current_streak_days")
    op.drop_column("users", "experience_points")
    op.drop_column("users", "display_name")
