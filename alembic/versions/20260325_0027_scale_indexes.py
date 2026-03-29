"""additional indexes for scale-sensitive api paths

Revision ID: 20260325_0027
Revises: 20260325_0026
Create Date: 2026-03-25 00:00:00.000000
"""

from alembic import op


revision = "20260325_0027"
down_revision = "20260325_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_roadmaps_user_goal_test", "roadmaps", ["user_id", "goal_id", "test_id"], unique=False)
    op.create_index("ix_diagnostic_tests_user_goal", "diagnostic_tests", ["user_id", "goal_id"], unique=False)
    op.create_index("ix_user_answers_test_question", "user_answers", ["test_id", "question_id"], unique=False)
    op.create_index("ix_topic_scores_tenant_topic_user", "topic_scores", ["tenant_id", "topic_id", "user_id"], unique=False)
    op.create_index("ix_feature_flags_tenant_feature", "feature_flags", ["tenant_id", "feature_name"], unique=False)
    op.create_index("ix_roadmap_steps_topic_status", "roadmap_steps", ["topic_id", "progress_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_roadmap_steps_topic_status", table_name="roadmap_steps")
    op.drop_index("ix_feature_flags_tenant_feature", table_name="feature_flags")
    op.drop_index("ix_topic_scores_tenant_topic_user", table_name="topic_scores")
    op.drop_index("ix_user_answers_test_question", table_name="user_answers")
    op.drop_index("ix_diagnostic_tests_user_goal", table_name="diagnostic_tests")
    op.drop_index("ix_roadmaps_user_goal_test", table_name="roadmaps")
