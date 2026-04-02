import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.autonomous_learning_agent_service import AutonomousLearningAgentService
from app.application.services.ai_request_service import AIRequestService
from app.application.services.hybrid_mentorship_service import HybridMentorshipService
from app.application.services.mentor_notification_service import MentorNotificationService
from app.application.services.mentor_service import MentorService
from app.core.dependencies import get_current_user, require_tenant_membership
from app.infrastructure.database import get_db_session
from app.infrastructure.jobs.dispatcher import enqueue_job
from app.infrastructure.repositories.mentor_chat_repository import MentorChatRepository
from app.infrastructure.repositories.mentor_message_repository import MentorMessageRepository
from app.infrastructure.repositories.mentor_student_repository import MentorStudentRepository
from app.infrastructure.repositories.user_repository import UserRepository
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
    MentorLearnerResponse,
    AutonomousAgentResponse,
    HybridMentorshipOverviewResponse,
    HybridSessionPlanRequest,
    HybridSessionPlanResponse,
)

router = APIRouter(prefix="/mentor", tags=["mentor"])
PRIVILEGED_LEARNER_ACCESS_ROLES = {"teacher", "admin", "super_admin"}


def _mentor_chat_meta(*, status_value: str, source: str) -> dict[str, bool | str]:
    return {
        "is_pending": status_value in {"queued", "processing", "received"},
        "is_terminal": status_value in {"completed", "failed", "timed_out", "fallback", "ready", "delivered", "acked"},
        "source": source,
    }


def _mentor_chat_response_from_result(*, request_id: str, result: dict, status_value: str) -> MentorChatResponse:
    return MentorChatResponse(
        request_id=request_id,
        status=status_value,
        reply=str(result.get("reply") or ""),
        advisor_type=str(result.get("advisor_type") or "MentorService"),
        used_ai=bool(result.get("used_ai")),
        fallback_used=bool(result.get("fallback_used")),
        fallback_reason=result.get("fallback_reason"),
        suggested_focus_topics=list(result.get("suggested_focus_topics") or []),
        why_recommended=list(result.get("why_recommended") or []),
        provider=result.get("provider"),
        latency_ms=result.get("latency_ms"),
        next_checkin_date=result.get("next_checkin_date"),
        session_summary=str(result.get("session_summary") or ""),
        memory_summary=dict(result.get("memory_summary") or {}),
    )


def _queued_mentor_chat_response(*, request_id: str, status_value: str, fallback_used: bool, fallback_reason: str | None, summary: str) -> MentorChatResponse:
    return MentorChatResponse(
        request_id=request_id,
        status=status_value,
        reply="",
        advisor_type="queued",
        used_ai=False,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        suggested_focus_topics=[],
        why_recommended=[],
        provider=None,
        latency_ms=None,
        next_checkin_date=None,
        session_summary=summary,
        memory_summary={},
    )


def _mentor_status_response(*, request_id: str, status_value: str, channel: str, reply: str | None, delivered: bool, acked: bool, source: str) -> MentorChatStatusResponse:
    return MentorChatStatusResponse(
        request_id=request_id,
        status=status_value,
        channel=channel,
        reply=reply,
        delivered=delivered,
        acked=acked,
        meta=_mentor_chat_meta(status_value=status_value, source=source),
    )


async def _queue_mentor_chat(
    *,
    db: AsyncSession,
    tenant_id: int,
    user_id: int,
    request_id: str,
    message: str,
    chat_history: list[dict[str, str]],
    channel: str,
) -> str:
    repository = MentorChatRepository(db)
    mentor_message_repo = MentorMessageRepository(db)

    await repository.upsert_message(
        tenant_id=tenant_id,
        user_id=user_id,
        request_id=request_id,
        direction="inbound",
        channel=channel,
        status="received",
        content=message,
        response_json={"chat_history": chat_history},
    )
    await mentor_message_repo.create_message(
        tenant_id=tenant_id,
        user_id=user_id,
        request_id=request_id,
        role="learner",
        message=message,
    )

    outbound = await repository.get_by_request(
        tenant_id=tenant_id,
        user_id=user_id,
        request_id=request_id,
        direction="outbound",
    )
    if outbound is None or outbound.status in {"failed"}:
        enqueue_job(
            task_name="jobs.process_mentor_chat",
            args=[tenant_id, user_id, request_id],
        )
    await db.commit()
    return request_id


async def _resolve_learner_id(
    *,
    db: AsyncSession,
    current_user,
    learner_id: int | None,
) -> int:
    effective_learner_id = learner_id or current_user.id
    if effective_learner_id == current_user.id and current_user.role.value == "student":
        return effective_learner_id
    if current_user.role.value in PRIVILEGED_LEARNER_ACCESS_ROLES:
        learner = await UserRepository(db).get_by_id_in_tenant(effective_learner_id, current_user.tenant_id)
        if learner is None or learner.role.value != "student":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learner not found")
        return effective_learner_id
    if current_user.role.value == "mentor":
        if await MentorStudentRepository(db).has_mapping(
            tenant_id=current_user.tenant_id,
            mentor_id=current_user.id,
            student_id=effective_learner_id,
        ):
            return effective_learner_id
        mapped_ids = await MentorStudentRepository(db).list_student_ids_for_mentor(
            tenant_id=current_user.tenant_id,
            mentor_id=current_user.id,
        )
        if learner_id is None and mapped_ids:
            return mapped_ids[0]
        if learner_id is None:
            return current_user.id
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/learners", response_model=list[MentorLearnerResponse])
async def mentor_learners(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    repository = UserRepository(db)
    if current_user.role.value in PRIVILEGED_LEARNER_ACCESS_ROLES:
        learners = await repository.list_by_tenant_and_roles(
            current_user.tenant_id,
            roles=[type(current_user.role).student],
            limit=200,
        )
    elif current_user.role.value == "mentor":
        learner_ids = await MentorStudentRepository(db).list_student_ids_for_mentor(
            tenant_id=current_user.tenant_id,
            mentor_id=current_user.id,
        )
        learners = await repository.get_by_ids_in_tenant(learner_ids, current_user.tenant_id)
        learners = [learner for learner in learners if learner.role.value == "student"]
    elif current_user.role.value == "student":
        learners = [current_user.user]
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return [
        {
            "user_id": int(learner.id),
            "email": learner.email,
            "display_name": learner.display_name or learner.email.split("@")[0],
        }
        for learner in learners
    ]


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
    if not hasattr(db, "execute"):
        result = await MentorService(session=db).chat(
            message=payload.message,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            chat_history=payload.chat_history,
        )
        return _mentor_chat_response_from_result(request_id=request_id, result=result, status_value="ready")
    queued = await AIRequestService(db).queue_mentor_chat(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        message=payload.message,
        chat_history=payload.chat_history,
        request_id=request_id,
        channel="http",
    )
    return _queued_mentor_chat_response(
        request_id=str(queued["request_id"]),
        status_value="processing",
        fallback_used=False,
        fallback_reason=None,
        summary="Mentor response is being processed asynchronously.",
    )


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
    repository = MentorChatRepository(db)
    outbound = await repository.get_by_request(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        request_id=request_id,
        direction="outbound",
    )
    if outbound is not None and outbound.content and outbound.status in {"ready", "delivered", "acked"}:
        payload_json = {}
        if outbound.response_json:
            try:
                parsed = json.loads(outbound.response_json)
                if isinstance(parsed, dict):
                    payload_json = parsed
            except json.JSONDecodeError:
                payload_json = {}
        payload_json["reply"] = outbound.content
        return _mentor_chat_response_from_result(
            request_id=request_id,
            result=payload_json,
            status_value=str(outbound.status),
        )

    await _queue_mentor_chat(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        request_id=request_id,
        message=payload.message,
        chat_history=payload.chat_history,
        channel="fallback",
    )
    return _queued_mentor_chat_response(
        request_id=request_id,
        status_value="queued",
        fallback_used=True,
        fallback_reason="still_processing",
        summary="Still waiting for async processing.",
    )


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
        ai_request = await AIRequestService(db).get_result(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            request_id=request_id,
        )
        if ai_request is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat delivery not found")
        result = ai_request.get("result") or {}
        return _mentor_status_response(
            request_id=request_id,
            status_value=str(ai_request.get("status") or "processing"),
            channel="http",
            reply=result.get("reply"),
            delivered=False,
            acked=False,
            source="ai_request",
        )
    return _mentor_status_response(
        request_id=row.request_id,
        status_value=row.status,
        channel=row.channel,
        reply=row.content or None,
        delivered=row.delivered_at is not None,
        acked=row.acked_at is not None,
        source="mentor_chat",
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
    return _mentor_status_response(
        request_id=row.request_id,
        status_value=row.status,
        channel=row.channel,
        reply=row.content or None,
        delivered=row.delivered_at is not None,
        acked=row.acked_at is not None,
        source="mentor_chat",
    )


@router.get("/suggestions", response_model=MentorSuggestionsResponse)
async def mentor_suggestions(
    learner_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    service = MentorService(session=db)
    effective_learner_id = await _resolve_learner_id(db=db, current_user=current_user, learner_id=learner_id)
    result = await service.contextual_suggestions(user_id=effective_learner_id, tenant_id=current_user.tenant_id)
    return MentorSuggestionsResponse(**result)


@router.get("/progress-analysis", response_model=MentorProgressAnalysisResponse)
async def mentor_progress_analysis(
    learner_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    service = MentorService(session=db)
    effective_learner_id = await _resolve_learner_id(db=db, current_user=current_user, learner_id=learner_id)
    result = await service.progress_analysis(user_id=effective_learner_id, tenant_id=current_user.tenant_id)
    return MentorProgressAnalysisResponse(**result)


@router.get("/notifications", response_model=MentorNotificationsResponse)
async def mentor_notifications(
    learner_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    service = MentorService(session=db)
    effective_learner_id = await _resolve_learner_id(db=db, current_user=current_user, learner_id=learner_id)

    roadmap_items = []
    if service.roadmap_repository is not None:
        roadmap_items = await service.roadmap_repository.list_user_roadmaps(
            user_id=effective_learner_id,
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
    progress = await service.progress_analysis(user_id=effective_learner_id, tenant_id=current_user.tenant_id)
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
    learner_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    effective_learner_id = await _resolve_learner_id(db=db, current_user=current_user, learner_id=learner_id)
    return await AutonomousLearningAgentService(db).run_cycle(
        user_id=effective_learner_id,
        tenant_id=current_user.tenant_id,
        execute_actions=False,
    )


@router.post("/agent/run", response_model=AutonomousAgentResponse)
async def mentor_agent_run(
    learner_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    effective_learner_id = await _resolve_learner_id(db=db, current_user=current_user, learner_id=learner_id)
    return await AutonomousLearningAgentService(db).run_cycle(
        user_id=effective_learner_id,
        tenant_id=current_user.tenant_id,
        execute_actions=True,
    )


@router.get("/hybrid-network", response_model=HybridMentorshipOverviewResponse)
async def hybrid_mentor_network(
    learner_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_tenant_membership),
):
    effective_learner_id = await _resolve_learner_id(db=db, current_user=current_user, learner_id=learner_id)
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
    effective_learner_id = await _resolve_learner_id(db=db, current_user=current_user, learner_id=payload.learner_id)
    return await HybridMentorshipService(db).build_session_plan(
        user_id=effective_learner_id,
        tenant_id=current_user.tenant_id,
        mentor_id=payload.mentor_id,
        topic_id=payload.topic_id,
    )
