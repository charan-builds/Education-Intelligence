from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class RoadmapStep(Base):
    __tablename__ = "roadmap_steps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    roadmap_id: Mapped[int] = mapped_column(ForeignKey("roadmaps.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="RESTRICT"), index=True)
    estimated_time_hours: Mapped[float] = mapped_column(Float, nullable=False, default=4.0)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    progress_status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")

    roadmap = relationship("Roadmap", back_populates="steps")
