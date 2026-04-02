from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class GamificationEvent(Base):
    __tablename__ = "gamification_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "idempotency_key", name="uq_gamification_events_tenant_user_idempotency"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    diagnostic_test_id: Mapped[int | None] = mapped_column(
        ForeignKey("diagnostic_tests.id", ondelete="SET NULL"), nullable=True, index=True
    )
    xp_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    level_after: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    streak_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="gamification_events")
