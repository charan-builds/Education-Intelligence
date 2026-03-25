import asyncio

from app.application.services.file_storage_service import FileStorageService
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
