import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.autonomous_learning_agent_service import AutonomousLearningAgentService
from app.application.services.hybrid_mentorship_service import HybridMentorshipService
from app.application.services.mentor_notification_service import MentorNotificationService
from app.application.services.mentor_service import MentorService
from app.core.dependencies import get_current_user, require_tenant_membership
from app.infrastructure.database import get_db_session
from app.infrastructure.repositories.mentor_chat_repository import MentorChatRepository
from app.infrastructure.repositories.mentor_message_repository import MentorMessageRepository
from app.realtime.hub import realtime_hub
from app.presentation.middleware.rate_limiter import limiter, rate_limit_key_by_ip, rate_limit_key_by_user
from app.schemas.mentor_schema import (
    MentorChatRequest,
    MentorChatAckRequest,
    MentorChatResponse,
    MentorChatStatusResponse,
    MentorNotificationsResponse,
    MentorProgressAnalysisResponse,
    MentorSuggestionsResponse,
    AutonomousAgentResponse,
    HybridMentorshipOverviewResponse,
    HybridSessionPlanRequest,
    HybridSessionPlanResponse,
)

router = APIRouter(prefix="/mentor", tags=["mentor"])


@router.post("/chat", response_model=MentorChatResponse)
@limiter.limit("20/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("40/minute", key_func=rate_limit_key_by_user)
async def mentor_chat(
    request: Request,
    payload: MentorChatRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    request_id = payload.request_id or f"http-{current_user.id}-{int(asyncio.get_running_loop().time() * 1000)}"
    tenant_id = current_user.tenant_id
    user_id = current_user.id

    repository = MentorChatRepository(db)
    mentor_message_repo = MentorMessageRepository(db)

    await repository.upsert_message(
        tenant_id=tenant_id,
        user_id=user_id,
        request_id=request_id,
        direction="inbound",
        channel="http",
        status="received",
        content=payload.message,
    )
    await mentor_message_repo.create_message(
        tenant_id=tenant_id,
        user_id=user_id,
        request_id=request_id,
        role="learner",
        message=payload.message,
    )

    result = await MentorService(session=db).chat(
        message=payload.message,
        user_id=user_id,
        tenant_id=tenant_id,
        chat_history=payload.chat_history,
    )
    result["request_id"] = request_id

    await mentor_message_repo.set_response(request_id=request_id, response=result["reply"], status="sent")

    outbound = await repository.upsert_message(
        tenant_id=tenant_id,
        user_id=user_id,
        request_id=request_id,
        direction="outbound",
        channel="http",
        status="ready",
        content=result["reply"],
        response_json=result,
    )
    await repository.mark_delivered(outbound)
    await db.commit()
    await realtime_hub.send_user(
        tenant_id,
        user_id,
        {
            "type": "mentor.response.ready",
            "request_id": request_id,
            "reply": result["reply"],
            "used_ai": result["used_ai"],
            "session_summary": result.get("session_summary", ""),
        },
    )
    if request_id and result.get("reply"):
        async def _stream_chunks() -> None:
            reply = str(result["reply"])
            for index in range(8, len(reply) + 8, 8):
                await realtime_hub.send_user(
                    tenant_id,
                    user_id,
                    {
                        "type": "mentor.response.chunk",
                        "request_id": request_id,
                        "content": reply[:index],
                        "done": index >= len(reply),
                    },
                )
                await asyncio.sleep(0.02)

        asyncio.create_task(_stream_chunks())
    return MentorChatResponse(**result)


@router.post("/chat/fallback", response_model=MentorChatResponse)
@limiter.limit("10/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("20/minute", key_func=rate_limit_key_by_user)
async def mentor_chat_fallback(
    request: Request,
    payload: MentorChatRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    request_id = payload.request_id or f"fallback-{current_user.id}-{int(asyncio.get_running_loop().time() * 1000)}"
    tenant_id = current_user.tenant_id
    user_id = current_user.id

    message_repo = MentorMessageRepository(db)
    existing_msg = await message_repo.get_by_request(request_id=request_id, tenant_id=tenant_id, user_id=user_id)
    if existing_msg is not None and existing_msg.response is not None:
        return MentorChatResponse(
            request_id=existing_msg.request_id,
            reply=existing_msg.response,
            advisor_type="fallback", 
            used_ai=False,
            fallback_used=True,
            fallback_reason="already_processed",
            suggested_focus_topics=[],
            why_recommended=[],
            provider=None,
            latency_ms=None,
            next_checkin_date=None,
            session_summary="",
            memory_summary={},
        )

    await message_repo.create_message(
        tenant_id=tenant_id,
        user_id=user_id,
        request_id=request_id,
        role="learner",
        message=payload.message,
    )

    result = await MentorService(session=db).chat(
        message=payload.message,
        user_id=user_id,
        tenant_id=tenant_id,
        chat_history=payload.chat_history,
    )
    result["request_id"] = request_id

    await message_repo.set_response(request_id=request_id, response=result.get("reply", ""), status="sent")
    await db.commit()

    return MentorChatResponse(**result)


@router.get("/chat/status/{request_id}", response_model=MentorChatStatusResponse)
async def mentor_chat_status(
    request_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    row = await MentorChatRepository(db).get_by_request(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        request_id=request_id,
        direction="outbound",
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat delivery not found")
    return MentorChatStatusResponse(
        request_id=row.request_id,
        status=row.status,
        channel=row.channel,
        reply=row.content or None,
        delivered=row.delivered_at is not None,
        acked=row.acked_at is not None,
    )


@router.post("/chat/ack", response_model=MentorChatStatusResponse)
async def mentor_chat_ack(
    payload: MentorChatAckRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    repository = MentorChatRepository(db)
    message_repo = MentorMessageRepository(db)
    row = await repository.get_by_request(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        request_id=payload.request_id,
        direction="outbound",
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat delivery not found")
    await repository.mark_acked(row)
    await message_repo.mark_acked(request_id=payload.request_id)
    await db.commit()
    return MentorChatStatusResponse(
        request_id=row.request_id,
        status=row.status,
        channel=row.channel,
        reply=row.content or None,
        delivered=row.delivered_at is not None,
        acked=row.acked_at is not None,
    )


@router.get("/suggestions", response_model=MentorSuggestionsResponse)
async def mentor_suggestions(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    service = MentorService(session=db)
    result = await service.contextual_suggestions(user_id=current_user.id, tenant_id=current_user.tenant_id)
    return MentorSuggestionsResponse(**result)


@router.get("/progress-analysis", response_model=MentorProgressAnalysisResponse)
async def mentor_progress_analysis(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    service = MentorService(session=db)
    result = await service.progress_analysis(user_id=current_user.id, tenant_id=current_user.tenant_id)
    return MentorProgressAnalysisResponse(**result)


@router.get("/notifications", response_model=MentorNotificationsResponse)
async def mentor_notifications(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    service = MentorService(session=db)

    roadmap_items = []
    if service.roadmap_repository is not None:
        roadmap_items = await service.roadmap_repository.list_user_roadmaps(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            limit=1,
            offset=0,
        )

    latest_roadmap = roadmap_items[0] if roadmap_items else None
    steps = []
    if latest_roadmap is not None:
        steps = [
            {
                "topic_id": step.topic_id,
                "progress_status": step.progress_status,
                "deadline": step.deadline,
            }
            for step in latest_roadmap.steps
        ]

    # Reuse progress analysis signals to derive weak topics when available.
    progress = await service.progress_analysis(user_id=current_user.id, tenant_id=current_user.tenant_id)
    topic_improvements = progress.get("topic_improvements", {})
    topic_scores = {int(topic_id): max(0.0, 70.0 - float(gap)) for topic_id, gap in topic_improvements.items()}

    notification_service = MentorNotificationService()
    notifications = notification_service.build_notifications(
        roadmap_steps=steps,
        topic_scores=topic_scores,
        last_activity_at=None,
    )

    return MentorNotificationsResponse(
        notifications=[
            {
                "trigger": item.trigger,
                "severity": item.severity,
                "title": item.title,
                "message": item.message,
            }
            for item in notifications
        ]
    )


@router.get("/agent/status", response_model=AutonomousAgentResponse)
async def mentor_agent_status(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    return await AutonomousLearningAgentService(db).run_cycle(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        execute_actions=False,
    )


@router.post("/agent/run", response_model=AutonomousAgentResponse)
async def mentor_agent_run(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    return await AutonomousLearningAgentService(db).run_cycle(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        execute_actions=True,
    )


@router.get("/hybrid-network", response_model=HybridMentorshipOverviewResponse)
async def hybrid_mentor_network(
    learner_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    effective_learner_id = learner_id or current_user.id
    privileged_roles = {"mentor", "teacher", "admin", "super_admin"}
    if effective_learner_id != current_user.id and current_user.role.value not in privileged_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return await HybridMentorshipService(db).get_overview(
        user_id=effective_learner_id,
        tenant_id=current_user.tenant_id,
    )


@router.post("/hybrid-network/session-plan", response_model=HybridSessionPlanResponse)
async def hybrid_mentor_session_plan(
    payload: HybridSessionPlanRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    effective_learner_id = payload.learner_id or current_user.id
    privileged_roles = {"mentor", "teacher", "admin", "super_admin"}
    if effective_learner_id != current_user.id and current_user.role.value not in privileged_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return await HybridMentorshipService(db).build_session_plan(
        user_id=effective_learner_id,
        tenant_id=current_user.tenant_id,
        mentor_id=payload.mentor_id,
        topic_id=payload.topic_id,
    )
