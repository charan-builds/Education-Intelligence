from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class DiscussionThread(Base):
    __tablename__ = "discussion_threads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"), index=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(default=False, nullable=False)
    upvotes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    best_answer_reply_id: Mapped[int | None] = mapped_column(ForeignKey("discussion_replies.id", ondelete="SET NULL"), nullable=True)
    is_ai_assisted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    community = relationship("Community", back_populates="threads")
    replies = relationship(
        "DiscussionReply",
        back_populates="thread",
        cascade="all, delete-orphan",
        foreign_keys="DiscussionReply.thread_id",
    )
