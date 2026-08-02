from collections.abc import Mapping

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.diagnostic_service import DiagnosticService
from app.core.dependencies import require_profile_completed
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
from app.schemas.question_serializer import normalize_difficulty_payload, sanitize_question

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


def _payload_to_dict(payload: object, fields: set[str]) -> dict:
    if isinstance(payload, Mapping):
        return dict(payload)
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    return {field: getattr(payload, field) for field in fields if hasattr(payload, field)}


def _sanitize_start_response(payload: object) -> DiagnosticStartResponse:
    data = _payload_to_dict(payload, set(DiagnosticStartResponse.model_fields))
    data["questions"] = [sanitize_question(question) for question in data.get("questions", [])]
    return DiagnosticStartResponse.model_validate(data)


def _sanitize_submit_response(payload: object) -> DiagnosticSubmitResponse:
    data = _payload_to_dict(payload, set(DiagnosticSubmitResponse.model_fields))
    data["questions"] = [sanitize_question(question) for question in data.get("questions", [])]
    answers = []
    for answer in data.get("answers", []):
        answer_data = _payload_to_dict(
            answer,
            {
                "question_id",
                "selected_answer",
                "score",
                "time_taken",
                "difficulty",
                "difficulty_weight",
                "difficulty_level",
                "difficulty_label",
            },
        )
        difficulty_level, difficulty_label = normalize_difficulty_payload(
            answer_data.get("difficulty", answer_data.get("difficulty_weight")),
            level=answer_data.get("difficulty_level"),
            label=answer_data.get("difficulty_label"),
        )
        answers.append(
            {
                "question_id": answer_data["question_id"],
                "selected_answer": answer_data["selected_answer"],
                "score": answer_data["score"],
                "time_taken": answer_data["time_taken"],
                "difficulty_level": difficulty_level,
                "difficulty_label": difficulty_label,
            }
        )
    data["answers"] = answers
    return DiagnosticSubmitResponse.model_validate(data)


def _sanitize_next_question_response(payload: object) -> DiagnosticQuestionResponse:
    return DiagnosticQuestionResponse.model_validate(sanitize_question(payload))


@router.post("/start", response_model=DiagnosticStartResponse)
@router.post("", response_model=DiagnosticStartResponse, include_in_schema=False)
@limiter.limit("50/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("100/minute", key_func=rate_limit_key_by_user)
async def start_diagnostic(
    request: Request,
    payload: DiagnosticStartRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_profile_completed),
):
    if payload.user_id is not None and payload.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot start a diagnostic for another user")
    result = await DiagnosticService(db).start_test_with_questions(
        user_id=current_user.id,
        goal_id=payload.goal_id,
        tenant_id=current_user.tenant_id,
        question_count=payload.question_count,
    )
    return _sanitize_start_response(result)


@router.post("/answer", response_model=DiagnosticAnswerResponse, deprecated=True)
@limiter.limit("50/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("100/minute", key_func=rate_limit_key_by_user)
async def answer_diagnostic_question(
    request: Request,
    payload: DiagnosticAnswerRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_profile_completed),
):
    # Compatibility endpoint: records progress for legacy step-by-step clients.
    # Canonical scoring happens only when /diagnostic/submit is called.
    return await DiagnosticService(db).answer_question(
        test_id=payload.test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        question_id=payload.question_id,
        user_answer=payload.user_answer,
        time_taken=payload.time_taken,
    )


@router.post("/submit", response_model=DiagnosticSubmitResponse)
@router.post("/complete", response_model=DiagnosticSubmitResponse, include_in_schema=False)
@limiter.limit("50/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("100/minute", key_func=rate_limit_key_by_user)
async def submit_diagnostic(
    request: Request,
    payload: DiagnosticSubmitRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_profile_completed),
):
    diagnostic_service = DiagnosticService(db)
    result = await diagnostic_service.submit_test(
        test_id=payload.test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        answers=[answer.model_dump() for answer in payload.answers] if payload.answers else None,
        trigger_roadmap=True,
    )
    return _sanitize_submit_response(result).model_dump()


@router.get("/result", response_model=DiagnosticResultResponse)
async def diagnostic_result(
    test_id: int = Query(...),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_profile_completed),
):
    result = await DiagnosticService(db).get_result(test_id, current_user.id, current_user.tenant_id)
    return DiagnosticResultResponse(**result)


@router.get("/{test_id}/performance")
async def diagnostic_performance(
    test_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_profile_completed),
):
    return await DiagnosticService(db).analyze_performance(
        test_id=test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )


@router.get("/{test_id}/gaps")
async def diagnostic_knowledge_gaps(
    test_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_profile_completed),
):
    return await DiagnosticService(db).detect_knowledge_gaps(
        test_id=test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )


@router.get("/{test_id}", response_model=DiagnosticResumeResponse)
async def get_diagnostic_session(
    test_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_profile_completed),
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
        "test_duration": getattr(test, "test_duration", 20),
        "status": getattr(test, "status", "started"),
        "completed_at": test.completed_at,
        "expired_at": getattr(test, "expired_at", None),
        "answered_count": len(answers),
    }


@router.get("/next/{test_id}", response_model=DiagnosticQuestionResponse | None, deprecated=True)
async def diagnostic_next_question_for_test(
    test_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_profile_completed),
):
    question = await DiagnosticService(db).get_next_question(
        test_id=test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    if question is None:
        return None
    return _sanitize_next_question_response(question)


@router.post("/next-question", response_model=DiagnosticQuestionResponse | None, deprecated=True)
async def diagnostic_next_question(
    payload: DiagnosticNextQuestionRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_profile_completed),
):
    question = await DiagnosticService(db).get_next_question(
        test_id=payload.test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    if question is None:
        return None
    return _sanitize_next_question_response(question)
