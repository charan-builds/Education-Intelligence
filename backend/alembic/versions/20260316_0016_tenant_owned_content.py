"""tenant-owned goals and topics

Revision ID: 20260316_0016
Revises: 20260316_0015
Create Date: 2026-03-16 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260316_0016"
down_revision: str | Sequence[str] | None = "20260316_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("goals", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.add_column("topics", sa.Column("tenant_id", sa.Integer(), nullable=True))

    op.execute("UPDATE goals SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.execute("UPDATE topics SET tenant_id = 1 WHERE tenant_id IS NULL")

    op.alter_column("goals", "tenant_id", nullable=False)
    op.alter_column("topics", "tenant_id", nullable=False)

    op.create_foreign_key("fk_goals_tenant_id_tenants", "goals", "tenants", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_topics_tenant_id_tenants", "topics", "tenants", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index(op.f("ix_goals_tenant_id"), "goals", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_topics_tenant_id"), "topics", ["tenant_id"], unique=False)

    op.drop_constraint("goals_name_key", "goals", type_="unique")
    op.drop_constraint("topics_name_key", "topics", type_="unique")
    op.create_unique_constraint("uq_goal_tenant_name", "goals", ["tenant_id", "name"])
    op.create_unique_constraint("uq_topic_tenant_name", "topics", ["tenant_id", "name"])


def downgrade() -> None:
    op.drop_constraint("uq_topic_tenant_name", "topics", type_="unique")
    op.drop_constraint("uq_goal_tenant_name", "goals", type_="unique")
    op.create_unique_constraint("topics_name_key", "topics", ["name"])
    op.create_unique_constraint("goals_name_key", "goals", ["name"])
    op.drop_index(op.f("ix_topics_tenant_id"), table_name="topics")
    op.drop_index(op.f("ix_goals_tenant_id"), table_name="goals")
    op.drop_constraint("fk_topics_tenant_id_tenants", "topics", type_="foreignkey")
    op.drop_constraint("fk_goals_tenant_id_tenants", "goals", type_="foreignkey")
    op.drop_column("topics", "tenant_id")
    op.drop_column("goals", "tenant_id")
