"""user tenant memberships

Revision ID: 20260325_0036
Revises: 20260325_0035
Create Date: 2026-03-25 00:00:03.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260325_0036"
down_revision = "20260325_0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = postgresql.ENUM("super_admin", "admin", "teacher", "mentor", "student", name="userrole", create_type=False)
    op.create_table(
        "user_tenant_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant_roles_user_tenant"),
    )
    op.create_index("ix_user_tenant_roles_id", "user_tenant_roles", ["id"], unique=False)
    op.create_index("ix_user_tenant_roles_user_id", "user_tenant_roles", ["user_id"], unique=False)
    op.create_index("ix_user_tenant_roles_tenant_id", "user_tenant_roles", ["tenant_id"], unique=False)
    op.add_column("users", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.execute(
        """
        INSERT INTO user_tenant_roles (user_id, tenant_id, role, created_at, updated_at)
        SELECT id, tenant_id, role, created_at, now()
        FROM users
        """
    )
    op.alter_column("users", "mfa_enabled", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "mfa_enabled")
    op.drop_index("ix_user_tenant_roles_tenant_id", table_name="user_tenant_roles")
    op.drop_index("ix_user_tenant_roles_user_id", table_name="user_tenant_roles")
    op.drop_index("ix_user_tenant_roles_id", table_name="user_tenant_roles")
    op.drop_table("user_tenant_roles")
