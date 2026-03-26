from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class MentorMessageStatus:
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    failed = "failed"


class MentorMessage(Base):
    __tablename__ = "mentor_messages"
    __table_args__ = (
        UniqueConstraint("request_id", name="uq_mentor_messages_request_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User")
    tenant = relationship("Tenant")
