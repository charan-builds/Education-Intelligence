"""performance indexes

Revision ID: 20260402_0014
Revises: 20260402_0013
Create Date: 2026-04-02 01:00:00.000000
"""

from alembic import op
from sqlalchemy import inspect


revision = "20260402_0014"
down_revision = "20260402_0013"
branch_labels = None
depends_on = None


def _create_index_if_missing(name: str, table_name: str, columns: list[str]) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if name in existing_indexes:
        return
    op.create_index(name, table_name, columns, unique=False)


def upgrade() -> None:
    _create_index_if_missing("ix_users_tenant_created_at", "users", ["tenant_id", "created_at"])
    _create_index_if_missing("ix_learning_events_tenant_user_event_ts", "learning_events", ["tenant_id", "user_id", "event_timestamp"])
    _create_index_if_missing("ix_diagnostic_tests_user_completed", "diagnostic_tests", ["user_id", "completed_at"])
    _create_index_if_missing("ix_diagnostic_tests_user_goal_open", "diagnostic_tests", ["user_id", "goal_id", "completed_at", "id"])
    _create_index_if_missing("ix_user_answers_test_question", "user_answers", ["test_id", "question_id"])
    _create_index_if_missing("ix_roadmaps_user_status_id", "roadmaps", ["user_id", "status", "id"])
    _create_index_if_missing("ix_roadmap_steps_roadmap_status_priority", "roadmap_steps", ["roadmap_id", "progress_status", "priority"])
    _create_index_if_missing("ix_roadmap_steps_roadmap_topic", "roadmap_steps", ["roadmap_id", "topic_id"])
    _create_index_if_missing("ix_questions_topic_difficulty_id", "questions", ["topic_id", "difficulty", "id"])
    _create_index_if_missing("ix_goal_topics_goal_topic", "goal_topics", ["goal_id", "topic_id"])
    _create_index_if_missing("ix_topic_prerequisites_topic_prereq", "topic_prerequisites", ["topic_id", "prerequisite_topic_id"])
    _create_index_if_missing("ix_community_members_tenant_community_user", "community_members", ["tenant_id", "community_id", "user_id"])
    _create_index_if_missing("ix_discussion_threads_tenant_community_created", "discussion_threads", ["tenant_id", "community_id", "created_at"])
    _create_index_if_missing("ix_discussion_replies_tenant_thread_created", "discussion_replies", ["tenant_id", "thread_id", "created_at"])
    _create_index_if_missing("ix_topic_scores_tenant_user_topic", "topic_scores", ["tenant_id", "user_id", "topic_id"])
    _create_index_if_missing("ix_topic_scores_tenant_user_updated", "topic_scores", ["tenant_id", "user_id", "updated_at"])
    _create_index_if_missing("ix_user_skill_vectors_tenant_user_topic", "user_skill_vectors", ["tenant_id", "user_id", "topic_id"])
    _create_index_if_missing("ix_user_skill_vectors_tenant_user_updated", "user_skill_vectors", ["tenant_id", "user_id", "last_updated"])
    _create_index_if_missing(
        "ix_analytics_snapshots_tenant_type_subject_updated",
        "analytics_snapshots",
        ["tenant_id", "snapshot_type", "subject_id", "updated_at"],
    )
    _create_index_if_missing("ix_outbox_events_status_available_id", "outbox_events", ["status", "available_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_outbox_events_status_available_id", table_name="outbox_events")
    op.drop_index("ix_analytics_snapshots_tenant_type_subject_updated", table_name="analytics_snapshots")
    op.drop_index("ix_user_skill_vectors_tenant_user_updated", table_name="user_skill_vectors")
    op.drop_index("ix_user_skill_vectors_tenant_user_topic", table_name="user_skill_vectors")
    op.drop_index("ix_topic_scores_tenant_user_updated", table_name="topic_scores")
    op.drop_index("ix_topic_scores_tenant_user_topic", table_name="topic_scores")
    op.drop_index("ix_discussion_replies_tenant_thread_created", table_name="discussion_replies")
    op.drop_index("ix_discussion_threads_tenant_community_created", table_name="discussion_threads")
    op.drop_index("ix_community_members_tenant_community_user", table_name="community_members")
    op.drop_index("ix_topic_prerequisites_topic_prereq", table_name="topic_prerequisites")
    op.drop_index("ix_goal_topics_goal_topic", table_name="goal_topics")
    op.drop_index("ix_questions_topic_difficulty_id", table_name="questions")
    op.drop_index("ix_roadmap_steps_roadmap_topic", table_name="roadmap_steps")
    op.drop_index("ix_roadmap_steps_roadmap_status_priority", table_name="roadmap_steps")
    op.drop_index("ix_roadmaps_user_status_id", table_name="roadmaps")
    op.drop_index("ix_user_answers_test_question", table_name="user_answers")
    op.drop_index("ix_diagnostic_tests_user_goal_open", table_name="diagnostic_tests")
    op.drop_index("ix_diagnostic_tests_user_completed", table_name="diagnostic_tests")
    op.drop_index("ix_learning_events_tenant_user_event_ts", table_name="learning_events")
    op.drop_index("ix_users_tenant_created_at", table_name="users")
