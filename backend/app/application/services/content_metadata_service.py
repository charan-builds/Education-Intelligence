from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.search_index_service import SearchIndexService
from app.core.sanitization import sanitize_text
from app.domain.models.content_metadata import ContentMetadata
from app.domain.models.file_asset import FileAsset
from app.domain.models.resource import Resource


class ContentMetadataService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.search_index_service = SearchIndexService(session)

    async def upsert_for_resource(
        self,
        *,
        tenant_id: int,
        resource_id: int,
        title: str | None,
        description: str | None,
        tags: list[str] | None,
        language_code: str | None,
        content_format: str | None,
        duration_seconds: int | None,
        source_url: str | None,
        checksum_sha256: str | None,
    ) -> ContentMetadata:
        row = await self._load_metadata(tenant_id=tenant_id, resource_id=resource_id, file_asset_id=None)
        now = datetime.now(timezone.utc)
        if row is None:
            row = ContentMetadata(
                tenant_id=tenant_id,
                resource_id=resource_id,
                file_asset_id=None,
                created_at=now,
                updated_at=now,
                tags_json="[]",
            )
            self.session.add(row)
        row.title = sanitize_text(title, max_length=255) if title else None
        row.description = sanitize_text(description, max_length=2000) if description else None
        row.tags_json = json.dumps([sanitize_text(tag, max_length=64) for tag in (tags or [])], ensure_ascii=True)
        row.language_code = sanitize_text(language_code, max_length=16) if language_code else None
        row.content_format = sanitize_text(content_format, max_length=64) if content_format else None
        row.duration_seconds = duration_seconds
        row.source_url = sanitize_text(source_url, max_length=1024) if source_url else None
        row.checksum_sha256 = sanitize_text(checksum_sha256, max_length=128) if checksum_sha256 else None
        row.updated_at = now
        await self.session.flush()
        await self.search_index_service.index_resource(tenant_id=tenant_id, resource_id=resource_id)
        await self.session.commit()
        return row

    async def upsert_for_file_asset(
        self,
        *,
        tenant_id: int,
        file_asset_id: int,
        title: str | None,
        description: str | None,
        tags: list[str] | None,
        language_code: str | None,
        content_format: str | None,
        duration_seconds: int | None,
        source_url: str | None,
        checksum_sha256: str | None,
    ) -> ContentMetadata:
        row = await self._load_metadata(tenant_id=tenant_id, resource_id=None, file_asset_id=file_asset_id)
        now = datetime.now(timezone.utc)
        if row is None:
            row = ContentMetadata(
                tenant_id=tenant_id,
                resource_id=None,
                file_asset_id=file_asset_id,
                created_at=now,
                updated_at=now,
                tags_json="[]",
            )
            self.session.add(row)
        row.title = sanitize_text(title, max_length=255) if title else None
        row.description = sanitize_text(description, max_length=2000) if description else None
        row.tags_json = json.dumps([sanitize_text(tag, max_length=64) for tag in (tags or [])], ensure_ascii=True)
        row.language_code = sanitize_text(language_code, max_length=16) if language_code else None
        row.content_format = sanitize_text(content_format, max_length=64) if content_format else None
        row.duration_seconds = duration_seconds
        row.source_url = sanitize_text(source_url, max_length=1024) if source_url else None
        row.checksum_sha256 = sanitize_text(checksum_sha256, max_length=128) if checksum_sha256 else None
        row.updated_at = now
        await self.session.flush()
        await self.search_index_service.index_file_asset(tenant_id=tenant_id, file_asset_id=file_asset_id)
        await self.session.commit()
        return row

    async def list_for_tenant(self, *, tenant_id: int, limit: int = 100) -> list[ContentMetadata]:
        result = await self.session.execute(
            select(ContentMetadata)
            .where(ContentMetadata.tenant_id == tenant_id)
            .order_by(ContentMetadata.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _load_metadata(self, *, tenant_id: int, resource_id: int | None, file_asset_id: int | None) -> ContentMetadata | None:
        stmt = select(ContentMetadata).where(ContentMetadata.tenant_id == tenant_id)
        if resource_id is not None:
            stmt = stmt.where(ContentMetadata.resource_id == resource_id)
        if file_asset_id is not None:
            stmt = stmt.where(ContentMetadata.file_asset_id == file_asset_id)
        return await self.session.scalar(stmt)

    async def validate_attachment(self, *, tenant_id: int, resource_id: int | None, file_asset_id: int | None) -> None:
        if resource_id is not None:
            resource = await self.session.get(Resource, resource_id)
            if resource is None or int(resource.tenant_id) != int(tenant_id):
                raise ValueError("Resource not found")
        if file_asset_id is not None:
            asset = await self.session.get(FileAsset, file_asset_id)
            if asset is None or int(asset.tenant_id) != int(tenant_id):
                raise ValueError("File asset not found")
