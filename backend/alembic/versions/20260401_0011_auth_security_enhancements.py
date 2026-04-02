"""auth security enhancements

Revision ID: 20260401_0011
Revises: 20260401_0010
Create Date: 2026-04-01 06:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260401_0011"
down_revision: Union[str, None] = "20260401_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_phone_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("token_jti", sa.String(length=64), nullable=False),
        sa.Column("device_info", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_token_jti", "refresh_tokens", ["token_jti"], unique=True)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_tenant_id", "refresh_tokens", ["tenant_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_is_revoked", "refresh_tokens", ["is_revoked"])

    op.create_table(
        "auth_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("detail", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_logs_tenant_id", "auth_logs", ["tenant_id"])
    op.create_index("ix_auth_logs_user_id", "auth_logs", ["user_id"])
    op.create_index("ix_auth_logs_email", "auth_logs", ["email"])
    op.create_index("ix_auth_logs_event_type", "auth_logs", ["event_type"])
    op.create_index("ix_auth_logs_status", "auth_logs", ["status"])
    op.create_index("ix_auth_logs_created_at", "auth_logs", ["created_at"])

    op.create_table(
        "token_blacklist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token_jti", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("token_type", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_token_blacklist_token_jti", "token_blacklist", ["token_jti"], unique=True)
    op.create_index("ix_token_blacklist_user_id", "token_blacklist", ["user_id"])
    op.create_index("ix_token_blacklist_tenant_id", "token_blacklist", ["tenant_id"])
    op.create_index("ix_token_blacklist_token_type", "token_blacklist", ["token_type"])
    op.create_index("ix_token_blacklist_expires_at", "token_blacklist", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_token_blacklist_expires_at", table_name="token_blacklist")
    op.drop_index("ix_token_blacklist_token_type", table_name="token_blacklist")
    op.drop_index("ix_token_blacklist_tenant_id", table_name="token_blacklist")
    op.drop_index("ix_token_blacklist_user_id", table_name="token_blacklist")
    op.drop_index("ix_token_blacklist_token_jti", table_name="token_blacklist")
    op.drop_table("token_blacklist")

    op.drop_index("ix_auth_logs_created_at", table_name="auth_logs")
    op.drop_index("ix_auth_logs_status", table_name="auth_logs")
    op.drop_index("ix_auth_logs_event_type", table_name="auth_logs")
    op.drop_index("ix_auth_logs_email", table_name="auth_logs")
    op.drop_index("ix_auth_logs_user_id", table_name="auth_logs")
    op.drop_index("ix_auth_logs_tenant_id", table_name="auth_logs")
    op.drop_table("auth_logs")

    op.drop_index("ix_refresh_tokens_is_revoked", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_tenant_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_jti", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
    op.drop_column("users", "is_phone_verified")
