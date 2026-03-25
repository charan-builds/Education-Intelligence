"""roadmap generation status and identity

Revision ID: 20260325_0026
Revises: 20260324_0025
Create Date: 2026-03-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0026"
down_revision = "20260324_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("roadmaps", sa.Column("test_id", sa.Integer(), nullable=True))
    op.add_column("roadmaps", sa.Column("status", sa.String(length=32), nullable=False, server_default="ready"))
    op.add_column("roadmaps", sa.Column("error_message", sa.String(length=500), nullable=True))
    op.create_index(op.f("ix_roadmaps_test_id"), "roadmaps", ["test_id"], unique=False)
    op.create_foreign_key("fk_roadmaps_test_id_diagnostic_tests", "roadmaps", "diagnostic_tests", ["test_id"], ["id"], ondelete="CASCADE")

    op.execute(
        """
        UPDATE roadmaps
        SET test_id = subquery.test_id
        FROM (
            SELECT DISTINCT ON (dt.user_id, dt.goal_id) dt.user_id, dt.goal_id, dt.id AS test_id
            FROM diagnostic_tests dt
            WHERE dt.completed_at IS NOT NULL
            ORDER BY dt.user_id, dt.goal_id, dt.completed_at DESC NULLS LAST, dt.id DESC
        ) AS subquery
        WHERE roadmaps.user_id = subquery.user_id
          AND roadmaps.goal_id = subquery.goal_id
          AND roadmaps.test_id IS NULL
        """
    )

    op.alter_column("roadmaps", "test_id", nullable=False)
    op.create_unique_constraint("uq_roadmaps_user_goal_test", "roadmaps", ["user_id", "goal_id", "test_id"])


def downgrade() -> None:
    op.drop_constraint("uq_roadmaps_user_goal_test", "roadmaps", type_="unique")
    op.drop_constraint("fk_roadmaps_test_id_diagnostic_tests", "roadmaps", type_="foreignkey")
    op.drop_index(op.f("ix_roadmaps_test_id"), table_name="roadmaps")
    op.drop_column("roadmaps", "error_message")
    op.drop_column("roadmaps", "status")
    op.drop_column("roadmaps", "test_id")
