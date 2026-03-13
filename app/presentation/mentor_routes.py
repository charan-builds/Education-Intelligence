from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.mentor_notification_service import MentorNotificationService
from app.application.services.mentor_service import MentorService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.schemas.mentor_schema import (
    MentorChatRequest,
    MentorChatResponse,
    MentorNotificationsResponse,
    MentorProgressAnalysisResponse,
    MentorSuggestionsResponse,
)

router = APIRouter(prefix="/mentor", tags=["mentor"])


@router.post("/chat", response_model=MentorChatResponse)
async def mentor_chat(
    payload: MentorChatRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if payload.user_id != current_user.id or payload.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    result = MentorService(session=db).chat(
        message=payload.message,
        user_id=payload.user_id,
        tenant_id=payload.tenant_id,
    )
    return MentorChatResponse(**result)


@router.get("/suggestions", response_model=MentorSuggestionsResponse)
async def mentor_suggestions(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    service = MentorService(session=db)
    guidance_text = await service.generate_advice(user_id=current_user.id, message="Provide concise next-step suggestions")

    # Deterministic split to produce UI-friendly bullet suggestions.
    chunks = [chunk.strip() for chunk in guidance_text.split(".") if chunk.strip()]
    suggestions = chunks[:4]
    if not suggestions:
        suggestions = [
            "Complete one pending roadmap step today.",
            "Revisit a weak topic and practice for 30 minutes.",
            "Write a short summary of what you learned.",
        ]
    return MentorSuggestionsResponse(suggestions=suggestions)


@router.get("/progress-analysis", response_model=MentorProgressAnalysisResponse)
async def mentor_progress_analysis(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    service = MentorService(session=db)
    result = await service.progress_analysis(user_id=current_user.id)
    return MentorProgressAnalysisResponse(**result)


@router.get("/notifications", response_model=MentorNotificationsResponse)
async def mentor_notifications(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
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
    progress = await service.progress_analysis(user_id=current_user.id)
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
