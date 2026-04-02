"""topic graph index fields

Revision ID: 20260311_0003
Revises: 20260311_0002
Create Date: 2026-03-11 00:00:01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260311_0003"
down_revision: Union[str, None] = "20260311_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("topics", sa.Column("depth", sa.Integer(), nullable=True))
    op.add_column("topics", sa.Column("graph_path", sa.String(length=512), nullable=True))
    op.create_index(op.f("ix_topics_depth"), "topics", ["depth"], unique=False)
    op.create_index(op.f("ix_topics_graph_path"), "topics", ["graph_path"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_topics_graph_path"), table_name="topics")
    op.drop_index(op.f("ix_topics_depth"), table_name="topics")
    op.drop_column("topics", "graph_path")
    op.drop_column("topics", "depth")
