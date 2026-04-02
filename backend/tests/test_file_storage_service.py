import asyncio

from app.application.services.file_storage_service import FileStorageService
from app.core.config import get_settings
from app.domain.models.file_asset import FileAsset


class _Session:
    def __init__(self):
        self.rows = {}
        self.next_id = 1

    def add(self, row):
        row.id = self.next_id
        self.rows[self.next_id] = row
        self.next_id += 1

    async def commit(self):
        return None

    async def flush(self):
        return None

    async def scalar(self, stmt):
        asset_id = list(stmt._where_criteria)[0].right.value
        return self.rows.get(asset_id)


def test_finalize_upload_updates_asset(monkeypatch):
    async def _run():
        session = _Session()
        service = FileStorageService(session)
        asset = FileAsset(
            tenant_id=1,
            uploaded_by_user_id=2,
            object_key="tenant/1/x/file.pdf",
            filename="file.pdf",
            content_type="application/pdf",
            storage_provider="s3",
            cdn_url="https://cdn.example/file.pdf",
            metadata_json="{}",
            created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
        session.add(asset)

        result = await service.finalize_upload(
            tenant_id=1,
            asset_id=asset.id,
            size_bytes=1234,
            metadata={"pages": 9},
        )

        assert result["size_bytes"] == 1234
        assert result["metadata"]["pages"] == 9

    asyncio.run(_run())


def test_create_upload_request_rejects_unsupported_content_type():
    async def _run():
        session = _Session()
        service = FileStorageService(session)
        try:
            await service.create_upload_request(
                tenant_id=1,
                user_id=2,
                filename="notes.exe",
                content_type="application/x-msdownload",
                metadata={},
            )
        except ValueError as exc:
            assert "Unsupported content type" in str(exc)
            return
        raise AssertionError("Expected ValueError")

    asyncio.run(_run())


def test_create_upload_request_returns_signed_upload_contract():
    async def _run():
        session = _Session()
        service = FileStorageService(session)
        result = await service.create_upload_request(
            tenant_id=1,
            user_id=2,
            filename="resume.pdf",
            content_type="application/pdf",
            metadata={"document_type": "resume"},
        )
        assert result["asset_id"] == 1
        assert result["upload_method"] == "PUT"
        assert result["upload_headers"]["Content-Type"] == "application/pdf"
        assert result["max_bytes"] == get_settings().upload_max_bytes

    asyncio.run(_run())


def test_finalize_upload_rejects_file_too_large():
    async def _run():
        session = _Session()
        service = FileStorageService(session)
        settings = get_settings()
        asset = FileAsset(
            tenant_id=1,
            uploaded_by_user_id=2,
            object_key="tenant/1/x/file.pdf",
            filename="file.pdf",
            content_type="application/pdf",
            storage_provider="s3",
            cdn_url="https://cdn.example/file.pdf",
            metadata_json="{}",
            created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
        session.add(asset)
        try:
            await service.finalize_upload(
                tenant_id=1,
                asset_id=asset.id,
                size_bytes=settings.upload_max_bytes + 1,
                metadata={},
            )
        except ValueError as exc:
            assert "maximum allowed size" in str(exc)
            return
        raise AssertionError("Expected ValueError")

    asyncio.run(_run())
