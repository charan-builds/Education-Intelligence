from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class ContentMetadata(Base):
    __tablename__ = "content_metadata"
    __table_args__ = (
        UniqueConstraint("resource_id", name="uq_content_metadata_resource_id"),
        UniqueConstraint("file_asset_id", name="uq_content_metadata_file_asset_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    resource_id: Mapped[int | None] = mapped_column(ForeignKey("resources.id", ondelete="CASCADE"), nullable=True, index=True)
    file_asset_id: Mapped[int | None] = mapped_column(ForeignKey("file_assets.id", ondelete="CASCADE"), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    language_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    content_format: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    search_document_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
