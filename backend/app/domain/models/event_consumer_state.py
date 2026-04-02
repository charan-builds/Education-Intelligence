from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class EventConsumerState(Base):
    __tablename__ = "event_consumer_states"
    __table_args__ = (
        UniqueConstraint("consumer_name", "message_id", name="uq_event_consumer_states_consumer_message"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    consumer_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    message_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    first_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
