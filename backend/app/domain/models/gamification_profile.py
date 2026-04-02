from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class GamificationProfile(Base):
    __tablename__ = "gamification_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_gamification_profiles_tenant_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_level_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xp_to_next_level: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    current_streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    longest_streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_activity_on: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    completed_topics_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_tests_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="gamification_profile")
