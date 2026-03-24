"""add mentor role to users

Revision ID: 20260318_0017
Revises: 20260316_0016
Create Date: 2026-03-18 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260318_0017"
down_revision: str | Sequence[str] | None = "20260316_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


OLD_USER_ROLE = sa.Enum("super_admin", "admin", "teacher", "student", name="userrole")
NEW_USER_ROLE = sa.Enum("super_admin", "admin", "teacher", "mentor", "student", name="userrole")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'mentor'")
        return

    NEW_USER_ROLE.create(bind, checkfirst=True)
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "role",
            existing_type=OLD_USER_ROLE,
            type_=NEW_USER_ROLE,
            existing_nullable=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    op.execute("UPDATE users SET role = 'teacher' WHERE role = 'mentor'")

    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE users ALTER COLUMN role TYPE TEXT")
        op.execute("DROP TYPE userrole")
        OLD_USER_ROLE.create(bind, checkfirst=False)
        op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole")
        return

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "role",
            existing_type=NEW_USER_ROLE,
            type_=OLD_USER_ROLE,
            existing_nullable=False,
        )
    NEW_USER_ROLE.drop(bind, checkfirst=True)
