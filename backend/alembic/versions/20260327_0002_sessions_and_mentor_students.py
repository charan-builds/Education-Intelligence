"""sessions and mentor-student mappings

Revision ID: 20260327_0002
Revises: 20260326_0001
Create Date: 2026-03-27 00:00:02.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260327_0002"
down_revision = "20260326_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("device", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"], unique=False)
    op.create_index("ix_sessions_tenant_id", "sessions", ["tenant_id"], unique=False)
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"], unique=False)
    op.create_index("ix_sessions_revoked", "sessions", ["revoked"], unique=False)

    op.create_table(
        "mentor_students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("mentor_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mentor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "mentor_id", "student_id", name="uq_mentor_students_tenant_mentor_student"),
    )
    op.create_index("ix_mentor_students_tenant_id", "mentor_students", ["tenant_id"], unique=False)
    op.create_index("ix_mentor_students_mentor_id", "mentor_students", ["mentor_id"], unique=False)
    op.create_index("ix_mentor_students_student_id", "mentor_students", ["student_id"], unique=False)

    op.create_index(
        "ix_outbox_events_status_available_id",
        "outbox_events",
        ["status", "available_at", "id"],
        unique=False,
    )
    op.execute(
        """
        WITH duplicate_open_tests AS (
            SELECT
                id,
                row_number() OVER (
                    PARTITION BY user_id, goal_id
                    ORDER BY started_at DESC NULLS LAST, id DESC
                ) AS row_num
            FROM diagnostic_tests
            WHERE completed_at IS NULL
        )
        UPDATE diagnostic_tests AS dt
        SET completed_at = now()
        FROM duplicate_open_tests AS duplicate
        WHERE dt.id = duplicate.id
          AND duplicate.row_num > 1
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_diagnostic_tests_open_user_goal")
    op.create_index(
        "ix_diagnostic_tests_open_user_goal",
        "diagnostic_tests",
        ["user_id", "goal_id"],
        unique=True,
        postgresql_where=sa.text("completed_at IS NULL"),
    )

    op.alter_column("sessions", "token_version", server_default=None)
    op.alter_column("sessions", "revoked", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_diagnostic_tests_open_user_goal", table_name="diagnostic_tests")
    op.drop_index("ix_outbox_events_status_available_id", table_name="outbox_events")

    op.drop_index("ix_mentor_students_student_id", table_name="mentor_students")
    op.drop_index("ix_mentor_students_mentor_id", table_name="mentor_students")
    op.drop_index("ix_mentor_students_tenant_id", table_name="mentor_students")
    op.drop_table("mentor_students")

    op.drop_index("ix_sessions_revoked", table_name="sessions")
    op.drop_index("ix_sessions_expires_at", table_name="sessions")
    op.drop_index("ix_sessions_tenant_id", table_name="sessions")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
