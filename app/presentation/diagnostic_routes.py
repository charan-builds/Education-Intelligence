from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.diagnostic_service import DiagnosticService
from app.application.services.outbox_service import OutboxService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.infrastructure.jobs.dispatcher import enqueue_job
from app.presentation.middleware.rate_limiter import limiter, rate_limit_key_by_ip, rate_limit_key_by_user
from app.schemas.diagnostic_schema import (
    DiagnosticNextQuestionRequest,
    DiagnosticQuestionResponse,
    DiagnosticResultResponse,
    DiagnosticStartRequest,
    DiagnosticStartResponse,
    DiagnosticSubmitRequest,
)

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


@router.post("/start", response_model=DiagnosticStartResponse)
@limiter.limit("50/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("100/minute", key_func=rate_limit_key_by_user)
async def start_diagnostic(
    request: Request,
    payload: DiagnosticStartRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await DiagnosticService(db).start_test(current_user.id, payload.goal_id, current_user.tenant_id)


@router.post("/submit", response_model=DiagnosticStartResponse)
@limiter.limit("50/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("100/minute", key_func=rate_limit_key_by_user)
async def submit_diagnostic(
    request: Request,
    payload: DiagnosticSubmitRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    test = await DiagnosticService(db).submit_answers(
        test_id=payload.test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        answers=[a.model_dump() for a in payload.answers],
    )
    queued = enqueue_job(
        "jobs.analyze_diagnostic",
        args=[payload.test_id, current_user.id, current_user.tenant_id],
    )
    if not queued:
        await OutboxService(db).add_task_event(
            task_name="jobs.analyze_diagnostic",
            args=[payload.test_id, current_user.id, current_user.tenant_id],
            tenant_id=current_user.tenant_id,
        )
        await db.commit()
    return test


@router.get("/result", response_model=DiagnosticResultResponse)
async def diagnostic_result(
    test_id: int = Query(...),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    scores = await DiagnosticService(db).get_result(test_id, current_user.id, current_user.tenant_id)
    return DiagnosticResultResponse(test_id=test_id, topic_scores=scores)


@router.post("/next-question", response_model=DiagnosticQuestionResponse | None)
async def diagnostic_next_question(
    payload: DiagnosticNextQuestionRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    question = await DiagnosticService(db).select_next_question(
        goal_id=payload.goal_id,
        previous_answers=[answer.model_dump() for answer in payload.previous_answers],
        tenant_id=current_user.tenant_id,
    )
    if question is None:
        return None
    return DiagnosticQuestionResponse(**question)
