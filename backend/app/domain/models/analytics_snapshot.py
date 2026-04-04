from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "snapshot_type",
            "subject_id",
            "window_start",
            "window_end",
            "snapshot_version",
            name="uq_analytics_snapshots_identity",
        ),
        Index(
            "ix_analytics_snapshots_tenant_snapshot_latest",
            "tenant_id",
            "snapshot_type",
            "is_latest",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    snapshot_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)


Index("ix_analytics_snapshots_created_at_desc", AnalyticsSnapshot.created_at.desc())
