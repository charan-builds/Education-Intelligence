from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.content_metadata_service import ContentMetadataService
from app.application.services.search_index_service import SearchIndexService
from app.core.authorization import require_permission
from app.infrastructure.database import get_db_session

router = APIRouter(prefix="/content", tags=["content"])


class ContentMetadataUpsertRequest(BaseModel):
    resource_id: int | None = Field(default=None, gt=0)
    file_asset_id: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    language_code: str | None = Field(default=None, max_length=16)
    content_format: str | None = Field(default=None, max_length=64)
    duration_seconds: int | None = Field(default=None, ge=0)
    source_url: str | None = Field(default=None, max_length=1024)
    checksum_sha256: str | None = Field(default=None, max_length=128)


class ContentIndexRequest(BaseModel):
    topic_id: int | None = Field(default=None, gt=0)
    resource_id: int | None = Field(default=None, gt=0)
    file_asset_id: int | None = Field(default=None, gt=0)


@router.post("/metadata")
async def upsert_content_metadata(
    payload: ContentMetadataUpsertRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_permission("files:upload")),
):
    service = ContentMetadataService(db)
    await service.validate_attachment(
        tenant_id=current_user.tenant_id,
        resource_id=payload.resource_id,
        file_asset_id=payload.file_asset_id,
    )
    if payload.resource_id is not None:
        row = await service.upsert_for_resource(
            tenant_id=current_user.tenant_id,
            resource_id=payload.resource_id,
            title=payload.title,
            description=payload.description,
            tags=payload.tags,
            language_code=payload.language_code,
            content_format=payload.content_format,
            duration_seconds=payload.duration_seconds,
            source_url=payload.source_url,
            checksum_sha256=payload.checksum_sha256,
        )
    elif payload.file_asset_id is not None:
        row = await service.upsert_for_file_asset(
            tenant_id=current_user.tenant_id,
            file_asset_id=payload.file_asset_id,
            title=payload.title,
            description=payload.description,
            tags=payload.tags,
            language_code=payload.language_code,
            content_format=payload.content_format,
            duration_seconds=payload.duration_seconds,
            source_url=payload.source_url,
            checksum_sha256=payload.checksum_sha256,
        )
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="resource_id or file_asset_id is required")
    return {"id": int(row.id), "resource_id": row.resource_id, "file_asset_id": row.file_asset_id}


@router.post("/index")
async def index_content(
    payload: ContentIndexRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_permission("search:query")),
):
    service = SearchIndexService(db)
    if payload.topic_id is not None:
        await service.index_topic(tenant_id=current_user.tenant_id, topic_id=payload.topic_id)
        return {"status": "indexed", "entity": "topic", "id": payload.topic_id}
    if payload.resource_id is not None:
        await service.index_resource(tenant_id=current_user.tenant_id, resource_id=payload.resource_id)
        return {"status": "indexed", "entity": "resource", "id": payload.resource_id}
    if payload.file_asset_id is not None:
        await service.index_file_asset(tenant_id=current_user.tenant_id, file_asset_id=payload.file_asset_id)
        return {"status": "indexed", "entity": "file_asset", "id": payload.file_asset_id}
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="topic_id, resource_id, or file_asset_id is required",
    )


@router.get("/metadata")
async def list_content_metadata(
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_permission("search:query")),
):
    rows = await ContentMetadataService(db).list_for_tenant(tenant_id=current_user.tenant_id, limit=limit)
    return {
        "items": [
            {
                "id": int(row.id),
                "resource_id": row.resource_id,
                "file_asset_id": row.file_asset_id,
                "title": row.title,
                "content_format": row.content_format,
                "updated_at": row.updated_at.isoformat(),
            }
            for row in rows
        ]
    }
