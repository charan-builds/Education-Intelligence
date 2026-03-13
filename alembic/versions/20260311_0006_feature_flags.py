"""feature flags table

Revision ID: 20260311_0006
Revises: 20260311_0005
Create Date: 2026-03-11 00:00:04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260311_0006"
down_revision: Union[str, None] = "20260311_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("feature_name", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "feature_name", name="uq_feature_flag_tenant_feature"),
    )
    op.create_index(op.f("ix_feature_flags_id"), "feature_flags", ["id"], unique=False)
    op.create_index(op.f("ix_feature_flags_tenant_id"), "feature_flags", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_feature_flags_feature_name"), "feature_flags", ["feature_name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_feature_flags_feature_name"), table_name="feature_flags")
    op.drop_index(op.f("ix_feature_flags_tenant_id"), table_name="feature_flags")
    op.drop_index(op.f("ix_feature_flags_id"), table_name="feature_flags")
    op.drop_table("feature_flags")
