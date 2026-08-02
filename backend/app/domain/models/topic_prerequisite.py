from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class TopicPrerequisite(Base):
    __tablename__ = "topic_prerequisites"
    __table_args__ = (UniqueConstraint("topic_id", "prerequisite_topic_id", name="uq_topic_prereq"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    prerequisite_topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    topic = relationship("Topic", foreign_keys=[topic_id], back_populates="prerequisite_edges")
    prerequisite_topic = relationship(
        "Topic", foreign_keys=[prerequisite_topic_id], back_populates="dependent_edges"
    )
