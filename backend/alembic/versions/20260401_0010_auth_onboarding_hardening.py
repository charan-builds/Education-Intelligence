"""auth onboarding hardening

Revision ID: 20260401_0010
Revises: 20260331_0009
Create Date: 2026-04-01 05:15:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260401_0010"
down_revision: Union[str, None] = "20260331_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'independent_learner'")
        auth_token_purpose = sa.Enum("email_verification", "password_reset", name="authtokenpurpose")
        auth_token_purpose.create(bind, checkfirst=True)

    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("is_profile_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("phone_number", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("linkedin_url", sa.String(length=1024), nullable=True))
    op.add_column("users", sa.Column("college_name", sa.String(length=255), nullable=True))
    op.execute("UPDATE users SET is_email_verified = true WHERE email_verified_at IS NOT NULL")

    auth_token_enum = (
        postgresql.ENUM("email_verification", "password_reset", name="authtokenpurpose", create_type=False)
        if bind.dialect.name == "postgresql"
        else sa.Enum("email_verification", "password_reset", name="authtokenpurpose")
    )
    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", auth_token_enum, nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"])
    op.create_index("ix_auth_tokens_tenant_id", "auth_tokens", ["tenant_id"])
    op.create_index("ix_auth_tokens_purpose", "auth_tokens", ["purpose"])
    op.create_index("ix_auth_tokens_token_hash", "auth_tokens", ["token_hash"], unique=True)
    op.create_index("ix_auth_tokens_expires_at", "auth_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_auth_tokens_expires_at", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_token_hash", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_purpose", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_tenant_id", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_user_id", table_name="auth_tokens")
    op.drop_table("auth_tokens")
    op.drop_column("users", "college_name")
    op.drop_column("users", "linkedin_url")
    op.drop_column("users", "phone_number")
    op.drop_column("users", "is_profile_completed")
    op.drop_column("users", "is_email_verified")
    op.drop_column("users", "full_name")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="authtokenpurpose").drop(bind, checkfirst=True)
