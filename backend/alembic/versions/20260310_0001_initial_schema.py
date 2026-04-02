"""initial schema

Revision ID: 20260310_0001
Revises: 
Create Date: 2026-03-10 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260310_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_type = sa.Enum("platform", "college", "company", "school", name="tenanttype")
    user_role = sa.Enum("super_admin", "admin", "teacher", "student", name="userrole")

    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_goals_id"), "goals", ["id"], unique=False)

    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", tenant_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_tenants_id"), "tenants", ["id"], unique=False)

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_topics_id"), "topics", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"], unique=False)

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questions_id"), "questions", ["id"], unique=False)
    op.create_index(op.f("ix_questions_topic_id"), "questions", ["topic_id"], unique=False)

    op.create_table(
        "topic_prerequisites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("prerequisite_topic_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["prerequisite_topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("topic_id", "prerequisite_topic_id", name="uq_topic_prereq"),
    )
    op.create_index(op.f("ix_topic_prerequisites_id"), "topic_prerequisites", ["id"], unique=False)
    op.create_index(op.f("ix_topic_prerequisites_prerequisite_topic_id"), "topic_prerequisites", ["prerequisite_topic_id"], unique=False)
    op.create_index(op.f("ix_topic_prerequisites_topic_id"), "topic_prerequisites", ["topic_id"], unique=False)

    op.create_table(
        "diagnostic_tests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_diagnostic_tests_goal_id"), "diagnostic_tests", ["goal_id"], unique=False)
    op.create_index(op.f("ix_diagnostic_tests_id"), "diagnostic_tests", ["id"], unique=False)
    op.create_index(op.f("ix_diagnostic_tests_user_id"), "diagnostic_tests", ["user_id"], unique=False)

    op.create_table(
        "roadmaps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roadmaps_goal_id"), "roadmaps", ["goal_id"], unique=False)
    op.create_index(op.f("ix_roadmaps_id"), "roadmaps", ["id"], unique=False)
    op.create_index(op.f("ix_roadmaps_user_id"), "roadmaps", ["user_id"], unique=False)

    op.create_table(
        "roadmap_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("roadmap_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("progress_status", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["roadmap_id"], ["roadmaps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roadmap_steps_id"), "roadmap_steps", ["id"], unique=False)
    op.create_index(op.f("ix_roadmap_steps_roadmap_id"), "roadmap_steps", ["roadmap_id"], unique=False)
    op.create_index(op.f("ix_roadmap_steps_topic_id"), "roadmap_steps", ["topic_id"], unique=False)

    op.create_table(
        "user_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("user_answer", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("time_taken", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_id"], ["diagnostic_tests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_answers_id"), "user_answers", ["id"], unique=False)
    op.create_index(op.f("ix_user_answers_question_id"), "user_answers", ["question_id"], unique=False)
    op.create_index(op.f("ix_user_answers_test_id"), "user_answers", ["test_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_answers_test_id"), table_name="user_answers")
    op.drop_index(op.f("ix_user_answers_question_id"), table_name="user_answers")
    op.drop_index(op.f("ix_user_answers_id"), table_name="user_answers")
    op.drop_table("user_answers")

    op.drop_index(op.f("ix_roadmap_steps_topic_id"), table_name="roadmap_steps")
    op.drop_index(op.f("ix_roadmap_steps_roadmap_id"), table_name="roadmap_steps")
    op.drop_index(op.f("ix_roadmap_steps_id"), table_name="roadmap_steps")
    op.drop_table("roadmap_steps")

    op.drop_index(op.f("ix_roadmaps_user_id"), table_name="roadmaps")
    op.drop_index(op.f("ix_roadmaps_id"), table_name="roadmaps")
    op.drop_index(op.f("ix_roadmaps_goal_id"), table_name="roadmaps")
    op.drop_table("roadmaps")

    op.drop_index(op.f("ix_diagnostic_tests_user_id"), table_name="diagnostic_tests")
    op.drop_index(op.f("ix_diagnostic_tests_id"), table_name="diagnostic_tests")
    op.drop_index(op.f("ix_diagnostic_tests_goal_id"), table_name="diagnostic_tests")
    op.drop_table("diagnostic_tests")

    op.drop_index(op.f("ix_topic_prerequisites_topic_id"), table_name="topic_prerequisites")
    op.drop_index(op.f("ix_topic_prerequisites_prerequisite_topic_id"), table_name="topic_prerequisites")
    op.drop_index(op.f("ix_topic_prerequisites_id"), table_name="topic_prerequisites")
    op.drop_table("topic_prerequisites")

    op.drop_index(op.f("ix_questions_topic_id"), table_name="questions")
    op.drop_index(op.f("ix_questions_id"), table_name="questions")
    op.drop_table("questions")

    op.drop_index(op.f("ix_users_tenant_id"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_topics_id"), table_name="topics")
    op.drop_table("topics")

    op.drop_index(op.f("ix_tenants_id"), table_name="tenants")
    op.drop_table("tenants")

    op.drop_index(op.f("ix_goals_id"), table_name="goals")
    op.drop_table("goals")

    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="tenanttype").drop(op.get_bind(), checkfirst=False)
