"""career engine job role mappings

Revision ID: 20260324_0023
Revises: 20260324_0022
Create Date: 2026-03-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260324_0023"
down_revision = "20260324_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False, server_default="generalist"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_job_role_tenant_name"),
    )
    op.create_table(
        "job_role_skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_role_id", sa.Integer(), sa.ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("job_role_id", "skill_id", name="uq_job_role_skill"),
    )


def downgrade() -> None:
    op.drop_table("job_role_skills")
    op.drop_table("job_roles")
