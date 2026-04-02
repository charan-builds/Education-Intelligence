"""user profile and mfa

Revision ID: 20260331_0009
Revises: 20260329_0008
Create Date: 2026-03-31 00:09:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260331_0009"
down_revision: Union[str, None] = "20260329_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_url", sa.String(length=1024), nullable=True))
    op.add_column("users", sa.Column("preferences_json", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("mfa_secret", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "mfa_secret")
    op.drop_column("users", "preferences_json")
    op.drop_column("users", "avatar_url")
