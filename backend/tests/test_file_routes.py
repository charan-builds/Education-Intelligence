import asyncio
from types import SimpleNamespace

from fastapi import HTTPException

from app.presentation import file_routes


class _FakeFileStorageService:
    def __init__(self, _db):
        self.db = _db

    async def create_upload_request(self, *, tenant_id: int, user_id: int, filename: str, content_type: str, metadata: dict | None = None):
        if content_type == "bad/type":
            raise ValueError("Unsupported content type")
        return {"asset_id": 1, "object_key": "tenant/1/file.pdf", "upload_url": "https://upload", "cdn_url": None}

    async def finalize_upload(self, *, tenant_id: int, asset_id: int, size_bytes: int | None, metadata: dict | None = None):
        if size_bytes and size_bytes > 100:
            raise ValueError("Uploaded file exceeds maximum allowed size")
        return {"asset_id": asset_id, "size_bytes": size_bytes}

    async def get_asset_download(self, *, tenant_id: int, asset_id: int):
        if asset_id == 404:
            raise ValueError("File asset not found")
        return {"asset_id": asset_id, "download_url": "https://download"}


def _user():
    return SimpleNamespace(id=4, tenant_id=2)


def test_file_routes_success_and_errors(monkeypatch):
    monkeypatch.setattr(file_routes, "FileStorageService", _FakeFileStorageService)

    async def _run():
        created = await file_routes.create_upload_request(
            payload=file_routes.FileUploadRequest(filename="notes.pdf", content_type="application/pdf", metadata={}),
            db=object(),
            current_user=_user(),
        )
        assert created["asset_id"] == 1

        finalized = await file_routes.finalize_upload(
            payload=file_routes.FileUploadFinalizeRequest(asset_id=1, size_bytes=42, metadata={}),
            db=object(),
            current_user=_user(),
        )
        assert finalized["size_bytes"] == 42

        download = await file_routes.get_file_download(
            asset_id=1,
            db=object(),
            current_user=_user(),
        )
        assert download["download_url"] == "https://download"

        try:
            await file_routes.create_upload_request(
                payload=file_routes.FileUploadRequest(filename="bad.bin", content_type="bad/type", metadata={}),
                db=object(),
                current_user=_user(),
            )
        except HTTPException as exc:
            assert exc.status_code == 400
        else:
            raise AssertionError("Expected HTTPException")

        try:
            await file_routes.get_file_download(
                asset_id=404,
                db=object(),
                current_user=_user(),
            )
        except HTTPException as exc:
            assert exc.status_code == 404
        else:
            raise AssertionError("Expected HTTPException")

    asyncio.run(_run())
