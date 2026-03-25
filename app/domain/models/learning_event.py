from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class LearningEvent(Base):
    __tablename__ = "learning_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "idempotency_key", name="uq_learning_events_tenant_user_idempotency"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    diagnostic_test_id: Mapped[int | None] = mapped_column(
        ForeignKey("diagnostic_tests.id", ondelete="SET NULL"), nullable=True, index=True
    )
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="v1")
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    event_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
