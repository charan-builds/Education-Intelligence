from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.file_storage_service import FileStorageService
from app.core.authorization import require_permission
from app.infrastructure.database import get_db_session
from pydantic import BaseModel, Field

router = APIRouter(prefix="/files", tags=["files"])


class FileUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=128)
    metadata: dict = Field(default_factory=dict)


class FileUploadFinalizeRequest(BaseModel):
    asset_id: int = Field(gt=0)
    size_bytes: int | None = Field(default=None, ge=0)
    metadata: dict = Field(default_factory=dict)


@router.post("/upload-request")
async def create_upload_request(
    payload: FileUploadRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_permission("files:upload")),
):
    try:
        return await FileStorageService(db).create_upload_request(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            filename=payload.filename,
            content_type=payload.content_type,
            metadata=payload.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/finalize")
async def finalize_upload(
    payload: FileUploadFinalizeRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_permission("files:upload")),
):
    try:
        return await FileStorageService(db).finalize_upload(
            tenant_id=current_user.tenant_id,
            asset_id=payload.asset_id,
            size_bytes=payload.size_bytes,
            metadata=payload.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{asset_id}")
async def get_file_download(
    asset_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_permission("files:upload")),
):
    try:
        return await FileStorageService(db).get_asset_download(
            tenant_id=current_user.tenant_id,
            asset_id=asset_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
