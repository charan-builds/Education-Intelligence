"""content search metadata

Revision ID: 20260325_0034
Revises: 20260325_0033
Create Date: 2026-03-25 07:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0034"
down_revision = "20260325_0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("file_asset_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("content_format", sa.String(length=64), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=128), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("search_document_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resource_id"], ["resources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_asset_id"], ["file_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resource_id", name="uq_content_metadata_resource_id"),
        sa.UniqueConstraint("file_asset_id", name="uq_content_metadata_file_asset_id"),
    )
    op.create_index("ix_content_metadata_tenant_id", "content_metadata", ["tenant_id"], unique=False)
    op.create_index("ix_content_metadata_resource_id", "content_metadata", ["resource_id"], unique=False)
    op.create_index("ix_content_metadata_file_asset_id", "content_metadata", ["file_asset_id"], unique=False)
    op.create_index("ix_content_metadata_content_format", "content_metadata", ["content_format"], unique=False)
    op.create_index("ix_content_metadata_checksum_sha256", "content_metadata", ["checksum_sha256"], unique=False)
    op.create_index("ix_content_metadata_search_document_id", "content_metadata", ["search_document_id"], unique=False)
    op.create_index("ix_content_metadata_created_at", "content_metadata", ["created_at"], unique=False)
    op.create_index("ix_content_metadata_updated_at", "content_metadata", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_content_metadata_updated_at", table_name="content_metadata")
    op.drop_index("ix_content_metadata_created_at", table_name="content_metadata")
    op.drop_index("ix_content_metadata_search_document_id", table_name="content_metadata")
    op.drop_index("ix_content_metadata_checksum_sha256", table_name="content_metadata")
    op.drop_index("ix_content_metadata_content_format", table_name="content_metadata")
    op.drop_index("ix_content_metadata_file_asset_id", table_name="content_metadata")
    op.drop_index("ix_content_metadata_resource_id", table_name="content_metadata")
    op.drop_index("ix_content_metadata_tenant_id", table_name="content_metadata")
    op.drop_table("content_metadata")
