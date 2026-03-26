from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "event_type", "idempotency_key", name="uq_outbox_events_tenant_event_idempotency"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
