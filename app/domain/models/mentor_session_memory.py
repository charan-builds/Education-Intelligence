from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class MentorSessionMemory(Base):
    __tablename__ = "mentor_session_memories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="mentor_chat")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    discussed_topics_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    mistakes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    insights_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="mentor_session_memories")
