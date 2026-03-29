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

    def _allowed_content_types(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.settings.upload_allowed_content_types.split(",")
            if item.strip()
        }

    def _sanitize_metadata(self, metadata: dict | None) -> dict:
        cleaned: dict[str, str | int | float | bool | None] = {}
        for key, value in list((metadata or {}).items())[: self.settings.upload_metadata_max_keys]:
            safe_key = sanitize_text(str(key), max_length=64).strip()
            if not safe_key:
                continue
            if isinstance(value, (int, float, bool)) or value is None:
                cleaned[safe_key] = value
            else:
                cleaned[safe_key] = sanitize_text(str(value), max_length=self.settings.upload_metadata_max_value_length)
        return cleaned

    def _build_s3_client(self):
        if boto3 is None or not self.settings.s3_bucket_name or not self.settings.s3_access_key_id or not self.settings.s3_secret_access_key:
            return None
        return boto3.client(
            "s3",
            endpoint_url=self.settings.s3_endpoint_url,
            aws_access_key_id=self.settings.s3_access_key_id,
            aws_secret_access_key=self.settings.s3_secret_access_key,
            region_name=self.settings.s3_region,
        )

    async def get_asset_download(self, *, tenant_id: int, asset_id: int) -> dict:
        asset = await self.session.scalar(
            select(FileAsset).where(
                FileAsset.id == asset_id,
                FileAsset.tenant_id == tenant_id,
            )
        )
        if asset is None:
            raise ValueError("File asset not found")
        download_url = asset.cdn_url
        client = self._build_s3_client()
        if client is not None:
            download_url = client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.settings.s3_bucket_name,
                    "Key": asset.object_key,
                    "ResponseContentType": asset.content_type,
                },
                ExpiresIn=int(self.settings.s3_presign_expiry_seconds),
            )
        return {
            "asset_id": int(asset.id),
            "filename": asset.filename,
            "content_type": asset.content_type,
            "size_bytes": asset.size_bytes,
            "download_url": download_url,
            "cdn_url": asset.cdn_url,
        }

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
        if not safe_filename or "/" in safe_filename or ".." in safe_filename:
            raise ValueError("Invalid filename")
        normalized_content_type = sanitize_text(content_type, max_length=128).strip().lower()
        if normalized_content_type not in self._allowed_content_types():
            raise ValueError("Unsupported content type")
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
            content_type=normalized_content_type,
            storage_provider="s3",
            cdn_url=cdn_url,
            metadata_json=json.dumps(self._sanitize_metadata(metadata), ensure_ascii=True, default=str),
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(asset)
        await self.session.commit()

        upload_url = None
        client = self._build_s3_client()
        if client is not None:
            upload_url = client.generate_presigned_url(
                ClientMethod="put_object",
                Params={"Bucket": self.settings.s3_bucket_name, "Key": object_key, "ContentType": normalized_content_type},
                ExpiresIn=int(self.settings.s3_presign_expiry_seconds),
            )
        return {
            "asset_id": int(asset.id),
            "object_key": object_key,
            "upload_url": upload_url,
            "upload_method": "PUT",
            "upload_headers": {"Content-Type": normalized_content_type},
            "cdn_url": cdn_url,
            "expires_in_seconds": int(self.settings.s3_presign_expiry_seconds),
            "max_bytes": int(self.settings.upload_max_bytes),
        }

    async def finalize_upload(
        self,
        *,
        tenant_id: int,
        asset_id: int,
        size_bytes: int | None,
        metadata: dict | None = None,
    ) -> dict:
        if size_bytes is not None and int(size_bytes) > int(self.settings.upload_max_bytes):
            raise ValueError("Uploaded file exceeds maximum allowed size")
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
        merged_metadata.update(self._sanitize_metadata(metadata))
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
