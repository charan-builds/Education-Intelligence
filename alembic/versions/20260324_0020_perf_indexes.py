"""performance indexes for scale-sensitive paths

Revision ID: 20260324_0020
Revises: 20260323_0019_topic_retention_reviews
Create Date: 2026-03-24 00:00:00.000000
"""

from alembic import op


revision = "20260324_0020"
down_revision = "20260323_0019_topic_retention_reviews"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_topic_scores_tenant_user_updated", "topic_scores", ["tenant_id", "user_id", "updated_at"], unique=False)
    op.create_index("ix_learning_events_tenant_user_created", "learning_events", ["tenant_id", "user_id", "created_at"], unique=False)
    op.create_index("ix_roadmap_steps_roadmap_status_priority", "roadmap_steps", ["roadmap_id", "progress_status", "priority"], unique=False)
    op.create_index("ix_discussion_threads_tenant_community_created", "discussion_threads", ["tenant_id", "community_id", "created_at"], unique=False)
    op.create_index("ix_discussion_replies_tenant_thread_created", "discussion_replies", ["tenant_id", "thread_id", "created_at"], unique=False)
    op.create_index("ix_goal_topics_goal_topic", "goal_topics", ["goal_id", "topic_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_goal_topics_goal_topic", table_name="goal_topics")
    op.drop_index("ix_discussion_replies_tenant_thread_created", table_name="discussion_replies")
    op.drop_index("ix_discussion_threads_tenant_community_created", table_name="discussion_threads")
    op.drop_index("ix_roadmap_steps_roadmap_status_priority", table_name="roadmap_steps")
    op.drop_index("ix_learning_events_tenant_user_created", table_name="learning_events")
    op.drop_index("ix_topic_scores_tenant_user_updated", table_name="topic_scores")
