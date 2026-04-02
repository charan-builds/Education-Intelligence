from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class MentorChatMessage(Base):
    __tablename__ = "mentor_chat_messages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "request_id", "direction", name="uq_mentor_chat_request_direction"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(16), nullable=False, default="websocket")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
