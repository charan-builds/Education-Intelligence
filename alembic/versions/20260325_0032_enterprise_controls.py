"""enterprise controls: audit, authz, file assets, advanced feature flags

Revision ID: 20260325_0032
Revises: 20260325_0031
Create Date: 2026-03-25 05:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0032"
down_revision = "20260325_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("feature_flags", sa.Column("rollout_percentage", sa.Integer(), nullable=False, server_default="100"))
    op.add_column("feature_flags", sa.Column("audience_filter_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("feature_flags", sa.Column("experiment_key", sa.String(length=128), nullable=True))
    op.create_index("ix_feature_flags_experiment_key", "feature_flags", ["experiment_key"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=128), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"], unique=False)
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource"], unique=False)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)

    op.create_table(
        "authorization_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("effect", sa.String(length=16), nullable=False, server_default="allow"),
        sa.Column("conditions_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "resource", "action", "subject", name="uq_authz_policy_identity"),
    )
    op.create_index("ix_authorization_policies_tenant_id", "authorization_policies", ["tenant_id"], unique=False)
    op.create_index("ix_authorization_policies_subject", "authorization_policies", ["subject"], unique=False)
    op.create_index("ix_authorization_policies_resource", "authorization_policies", ["resource"], unique=False)
    op.create_index("ix_authorization_policies_action", "authorization_policies", ["action"], unique=False)
    op.create_index("ix_authorization_policies_created_at", "authorization_policies", ["created_at"], unique=False)

    op.create_table(
        "file_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("storage_provider", sa.String(length=32), nullable=False, server_default="s3"),
        sa.Column("cdn_url", sa.String(length=1024), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index("ix_file_assets_tenant_id", "file_assets", ["tenant_id"], unique=False)
    op.create_index("ix_file_assets_uploaded_by_user_id", "file_assets", ["uploaded_by_user_id"], unique=False)
    op.create_index("ix_file_assets_object_key", "file_assets", ["object_key"], unique=False)
    op.create_index("ix_file_assets_created_at", "file_assets", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_file_assets_created_at", table_name="file_assets")
    op.drop_index("ix_file_assets_object_key", table_name="file_assets")
    op.drop_index("ix_file_assets_uploaded_by_user_id", table_name="file_assets")
    op.drop_index("ix_file_assets_tenant_id", table_name="file_assets")
    op.drop_table("file_assets")

    op.drop_index("ix_authorization_policies_created_at", table_name="authorization_policies")
    op.drop_index("ix_authorization_policies_action", table_name="authorization_policies")
    op.drop_index("ix_authorization_policies_resource", table_name="authorization_policies")
    op.drop_index("ix_authorization_policies_subject", table_name="authorization_policies")
    op.drop_index("ix_authorization_policies_tenant_id", table_name="authorization_policies")
    op.drop_table("authorization_policies")

    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_feature_flags_experiment_key", table_name="feature_flags")
    op.drop_column("feature_flags", "experiment_key")
    op.drop_column("feature_flags", "audience_filter_json")
    op.drop_column("feature_flags", "rollout_percentage")
