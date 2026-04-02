from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class StreamConsumerOffset(Base):
    __tablename__ = "stream_consumer_offsets"
    __table_args__ = (
        UniqueConstraint("consumer_group", "topic", "partition", name="uq_stream_consumer_offsets_group_topic_partition"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    consumer_group: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    partition: Mapped[int] = mapped_column(Integer, nullable=False)
    offset: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
