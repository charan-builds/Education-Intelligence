from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_goal_tenant_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skills_covered: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    estimated_duration_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_tag: Mapped[str | None] = mapped_column(String(32), nullable=True)
    roadmap_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
