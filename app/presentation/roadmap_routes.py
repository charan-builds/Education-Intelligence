from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.roadmap_service import RoadmapService
from app.application.services.outbox_service import OutboxService
from app.core.dependencies import get_current_user, get_pagination_params
from app.infrastructure.database import get_db_session
from app.infrastructure.jobs.dispatcher import enqueue_job
from app.realtime.hub import realtime_hub
from app.presentation.middleware.rate_limiter import limiter, rate_limit_key_by_ip, rate_limit_key_by_user
from app.schemas.common_schema import PaginationParams
from app.schemas.roadmap_schema import (
    AdaptiveRoadmapResponse,
    RoadmapGenerateRequest,
    RoadmapPageResponse,
    RoadmapResponse,
    RoadmapStepResponse,
    RoadmapStepUpdateRequest,
)

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.post("/generate", response_model=RoadmapResponse)
@limiter.limit("50/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("100/minute", key_func=rate_limit_key_by_user)
async def generate_roadmap(
    request: Request,
    payload: RoadmapGenerateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    roadmap = await RoadmapService(db).generate(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        goal_id=payload.goal_id,
        test_id=payload.test_id,
    )
    outbox_service = OutboxService(db)

    roadmap_steps = [
        {
            "topic_id": int(step.topic_id),
            "progress_status": str(step.progress_status),
            "deadline": step.deadline.isoformat(),
            "priority": int(step.priority),
        }
        for step in roadmap.steps
    ]
    queued_notify = enqueue_job(
        "jobs.send_notifications",
        kwargs={
            "roadmap_steps": roadmap_steps,
            "topic_scores": {},
            "last_activity_at_iso": None,
        },
    )
    if not queued_notify:
        await outbox_service.add_task_event(
            task_name="jobs.send_notifications",
            kwargs={
                "roadmap_steps": roadmap_steps,
                "topic_scores": {},
                "last_activity_at_iso": None,
            },
            tenant_id=current_user.tenant_id,
        )
    if not queued_notify:
        await db.commit()
    return roadmap


@router.get("/{user_id}", response_model=RoadmapPageResponse)
async def list_roadmaps(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    if user_id != current_user.id and current_user.role.value not in {"admin", "super_admin", "teacher"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return await RoadmapService(db).list_for_user_page(
        user_id=user_id,
        tenant_id=current_user.tenant_id,
        limit=pagination.limit,
        offset=pagination.offset,
        cursor=pagination.cursor,
    )


@router.patch("/steps/{step_id}", response_model=RoadmapStepResponse)
async def update_roadmap_step(
    step_id: int,
    payload: RoadmapStepUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if current_user.role.value != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can update roadmap progress")
    result = await RoadmapService(db).update_step_status(
        step_id=step_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        progress_status=payload.progress_status,
    )
    await realtime_hub.send_user(
        current_user.tenant_id,
        current_user.id,
        {
            "type": "progress.updated",
            "step_id": result["id"],
            "topic_id": result["topic_id"],
            "progress_status": result["progress_status"],
        },
    )
    await realtime_hub.send_tenant(
        current_user.tenant_id,
        {
            "type": "activity.created",
            "scope": "tenant",
            "event_type": "roadmap_step_updated",
            "user_id": current_user.id,
            "topic_id": result["topic_id"],
            "message": f"User {current_user.id} moved topic {result['topic_id']} to {result['progress_status']}.",
        },
    )
    return result


@router.post("/adaptive-refresh", response_model=AdaptiveRoadmapResponse)
async def adaptive_refresh_roadmap(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if current_user.role.value != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can adapt roadmap progress")
    return await RoadmapService(db).adapt_latest(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
