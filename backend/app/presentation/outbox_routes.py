from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.outbox_service import OutboxService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.schemas.outbox_schema import (
    OutboxEventPageResponse,
    OutboxFlushResponse,
    OutboxRecoverResponse,
    OutboxRequeueOneResponse,
    OutboxRequeueResponse,
    OutboxStatsResponse,
)

router = APIRouter(prefix="/ops/outbox", tags=["ops"])


@router.get("", response_model=OutboxEventPageResponse)
async def list_outbox_events(
    event_status: str = Query("pending", pattern="^(pending|processing|dead|dispatched)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    tenant_scope = None if current_user.role.value == "super_admin" else int(current_user.tenant_id)
    items = await OutboxService(db).list_events(
        status=event_status,
        tenant_id=tenant_scope,
        limit=limit,
        offset=offset,
    )
    return OutboxEventPageResponse(items=items)


@router.post("/flush", response_model=OutboxFlushResponse)
async def flush_outbox_events(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    dispatched = await OutboxService(db).flush_pending_events(limit=limit)
    return OutboxFlushResponse(dispatched=dispatched)


@router.post("/requeue-dead", response_model=OutboxRequeueResponse)
async def requeue_dead_outbox_events(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    tenant_scope = None if current_user.role.value == "super_admin" else int(current_user.tenant_id)
    requeued = await OutboxService(db).requeue_dead_events(tenant_id=tenant_scope, limit=limit)
    return OutboxRequeueResponse(requeued=requeued)


@router.get("/stats", response_model=OutboxStatsResponse)
async def outbox_stats(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    tenant_scope = None if current_user.role.value == "super_admin" else int(current_user.tenant_id)
    stats = await OutboxService(db).get_stats(tenant_id=tenant_scope)
    return OutboxStatsResponse(**stats)


@router.post("/requeue-dead/{event_id}", response_model=OutboxRequeueOneResponse)
async def requeue_one_dead_outbox_event(
    event_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    tenant_scope = None if current_user.role.value == "super_admin" else int(current_user.tenant_id)
    requeued = await OutboxService(db).requeue_dead_event_by_id(event_id=event_id, tenant_id=tenant_scope)
    if not requeued:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dead outbox event not found")
    return OutboxRequeueOneResponse(requeued=True)


@router.post("/recover-stuck", response_model=OutboxRecoverResponse)
async def recover_stuck_outbox_events(
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    recovered = await OutboxService(db).recover_stuck_processing_events(limit=limit)
    return OutboxRecoverResponse(recovered=recovered)
