from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class MentorMemoryProfile(Base):
    __tablename__ = "mentor_memory_profiles"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_mentor_memory_profile_tenant_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    learner_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    weak_topics_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    strong_topics_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    past_mistakes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    improvement_signals_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    preferred_learning_style: Mapped[str] = mapped_column(String(64), nullable=False, default="balanced")
    learning_speed: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_session_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="mentor_memory_profiles")
