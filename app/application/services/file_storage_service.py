from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.search_index_service import SearchIndexService
from app.core.config import get_settings
from app.core.sanitization import sanitize_text
from app.domain.models.file_asset import FileAsset

try:  # pragma: no cover
    import boto3
except Exception:  # pragma: no cover
    boto3 = None  # type: ignore


class FileStorageService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.search_index_service = SearchIndexService(session)

    async def create_upload_request(
        self,
        *,
        tenant_id: int,
        user_id: int,
        filename: str,
        content_type: str,
        metadata: dict | None = None,
    ) -> dict:
        safe_filename = sanitize_text(filename, max_length=200)
        object_key = f"tenant/{tenant_id}/{uuid4().hex}/{safe_filename}"
        cdn_url = (
            f"{self.settings.cdn_base_url.rstrip('/')}/{object_key}"
            if self.settings.cdn_base_url
            else None
        )
        asset = FileAsset(
            tenant_id=tenant_id,
            uploaded_by_user_id=user_id,
            object_key=object_key,
            filename=safe_filename,
            content_type=content_type,
            storage_provider="s3",
            cdn_url=cdn_url,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=True, default=str),
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(asset)
        await self.session.commit()

        upload_url = None
        if boto3 is not None and self.settings.s3_bucket_name and self.settings.s3_access_key_id and self.settings.s3_secret_access_key:
            client = boto3.client(
                "s3",
                endpoint_url=self.settings.s3_endpoint_url,
                aws_access_key_id=self.settings.s3_access_key_id,
                aws_secret_access_key=self.settings.s3_secret_access_key,
                region_name=self.settings.s3_region,
            )
            upload_url = client.generate_presigned_url(
                ClientMethod="put_object",
                Params={"Bucket": self.settings.s3_bucket_name, "Key": object_key, "ContentType": content_type},
                ExpiresIn=int(timedelta(minutes=15).total_seconds()),
            )
        return {
            "asset_id": int(asset.id),
            "object_key": object_key,
            "upload_url": upload_url,
            "cdn_url": cdn_url,
        }

    async def finalize_upload(
        self,
        *,
        tenant_id: int,
        asset_id: int,
        size_bytes: int | None,
        metadata: dict | None = None,
    ) -> dict:
        asset = await self.session.scalar(
            select(FileAsset).where(
                FileAsset.id == asset_id,
                FileAsset.tenant_id == tenant_id,
            )
        )
        if asset is None:
            raise ValueError("File asset not found")
        asset.size_bytes = size_bytes
        merged_metadata = json.loads(asset.metadata_json or "{}")
        merged_metadata.update(metadata or {})
        asset.metadata_json = json.dumps(merged_metadata, ensure_ascii=True, default=str)
        await self.session.flush()
        if self.settings.search_backend.lower() != "db":
            await self.search_index_service.index_file_asset(tenant_id=tenant_id, file_asset_id=int(asset.id))
        await self.session.commit()
        return {
            "asset_id": int(asset.id),
            "object_key": asset.object_key,
            "cdn_url": asset.cdn_url,
            "size_bytes": asset.size_bytes,
            "metadata": merged_metadata,
        }
