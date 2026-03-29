from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.diagnostic_service import DiagnosticService
from app.application.services.outbox_service import OutboxService
from app.application.services.roadmap_service import RoadmapService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.presentation.middleware.rate_limiter import limiter, rate_limit_key_by_ip, rate_limit_key_by_user
from app.schemas.diagnostic_schema import (
    DiagnosticAnswerRequest,
    DiagnosticAnswerResponse,
    DiagnosticNextQuestionRequest,
    DiagnosticQuestionResponse,
    DiagnosticResultResponse,
    DiagnosticResumeResponse,
    DiagnosticStartRequest,
    DiagnosticStartResponse,
    DiagnosticSubmitResponse,
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


@router.get("/{test_id}", response_model=DiagnosticResumeResponse)
async def get_diagnostic_session(
    test_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    test, answers = await DiagnosticService(db).get_or_resume_test(
        test_id=test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    return {
        "id": test.id,
        "user_id": test.user_id,
        "goal_id": test.goal_id,
        "started_at": test.started_at,
        "completed_at": test.completed_at,
        "answered_count": len(answers),
    }


@router.post("/answer", response_model=DiagnosticAnswerResponse)
@limiter.limit("50/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("100/minute", key_func=rate_limit_key_by_user)
async def answer_diagnostic_question(
    request: Request,
    payload: DiagnosticAnswerRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await DiagnosticService(db).answer_question(
        test_id=payload.test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        question_id=payload.question_id,
        user_answer=payload.user_answer,
        time_taken=payload.time_taken,
    )


@router.post("/submit", response_model=DiagnosticSubmitResponse)
@limiter.limit("50/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("100/minute", key_func=rate_limit_key_by_user)
async def submit_diagnostic(
    request: Request,
    payload: DiagnosticSubmitRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    result = await DiagnosticService(db).finalize_test(
        test_id=payload.test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    _, should_enqueue = await RoadmapService(db).ensure_generation_requested(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        goal_id=result["goal_id"],
        test_id=payload.test_id,
    )
    if should_enqueue:
        # Always enqueue via transactional outbox to make dispatch idempotent.
        await OutboxService(db).add_task_event(
            task_name="jobs.generate_roadmap",
            args=[current_user.id, current_user.tenant_id, result["goal_id"], payload.test_id],
            tenant_id=current_user.tenant_id,
            idempotency_key=f"roadmap-generate:{current_user.id}:{result['goal_id']}:{payload.test_id}",
        )
        await db.commit()
    return result


@router.get("/result", response_model=DiagnosticResultResponse)
async def diagnostic_result(
    test_id: int = Query(...),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    result = await DiagnosticService(db).get_result(test_id, current_user.id, current_user.tenant_id)
    return DiagnosticResultResponse(**result)


@router.get("/next/{test_id}", response_model=DiagnosticQuestionResponse | None)
async def diagnostic_next_question_for_test(
    test_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    question = await DiagnosticService(db).get_next_question(
        test_id=test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    if question is None:
        return None
    return DiagnosticQuestionResponse(**question)


@router.post("/next-question", response_model=DiagnosticQuestionResponse | None, deprecated=True)
async def diagnostic_next_question(
    payload: DiagnosticNextQuestionRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    question = await DiagnosticService(db).get_next_question(
        test_id=payload.test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    if question is None:
        return None
    return DiagnosticQuestionResponse(**question)
