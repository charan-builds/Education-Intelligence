from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class TopicFeature(Base):
    __tablename__ = "topic_features"
    __table_args__ = (
        UniqueConstraint("tenant_id", "topic_id", "feature_set_name", name="uq_topic_features_tenant_topic_feature_set"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    feature_set_name: Mapped[str] = mapped_column(String(64), nullable=False, default="topic_features")
    feature_values_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
