import json
import inspect

from fastapi import APIRouter, Body, Depends, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.topic_knowledge_service import TopicKnowledgeService
from app.application.services.topic_service import TopicService
from app.core.dependencies import get_current_user, get_pagination_params, require_roles
from app.infrastructure.database import get_db_session
from app.schemas.common_schema import PaginationParams
from app.schemas.topic_schema import (
    AIQuestionGenerationRequest,
    AIQuestionGenerationResponse,
    KnowledgeGraphResponse,
    QuestionCreateRequest,
    QuestionImportRequest,
    QuestionImportResponse,
    QuestionPageResponse,
    QuestionResponse,
    QuestionUpdateRequest,
    TopicCreateRequest,
    TopicDetailResponse,
    TopicExplanationRequest,
    TopicExplanationResponse,
    TopicPageResponse,
    TopicPrerequisiteCreateRequest,
    TopicPrerequisitePageResponse,
    TopicPrerequisiteResponse,
    TopicReasoningResponse,
    TopicSummaryResponse,
    TopicUpdateRequest,
)

router = APIRouter(prefix="/topics", tags=["topics"])


async def _call_topic_service(method, *, tenant_id: int, user_id: int | None = None, **kwargs):
    try:
        signature = inspect.signature(method)
        if "tenant_id" in signature.parameters:
            kwargs["tenant_id"] = tenant_id
        if user_id is not None and "user_id" in signature.parameters:
            kwargs["user_id"] = user_id
    except (TypeError, ValueError):
        pass
    return await method(**kwargs)


@router.get("", response_model=TopicPageResponse)
async def list_topics(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await TopicService(db).list_topics_page(
        limit=pagination.limit,
        offset=pagination.offset,
        tenant_id=current_user.tenant_id,
    )


@router.get("/graph", response_model=KnowledgeGraphResponse)
async def get_topic_graph(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await TopicKnowledgeService(db).get_graph_snapshot(
        tenant_id=current_user.tenant_id,
        user_id=getattr(current_user, "id", None),
    )


@router.get("/reasoning/{topic_id}", response_model=TopicReasoningResponse)
async def get_topic_reasoning(
    topic_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await TopicKnowledgeService(db).explain_reasoning(
        tenant_id=current_user.tenant_id,
        user_id=getattr(current_user, "id", None),
        topic_id=topic_id,
    )


@router.post("", response_model=TopicSummaryResponse)
async def create_topic(
    payload: TopicCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    return await _call_topic_service(
        TopicService(db).create_topic,
        tenant_id=_current_user.tenant_id,
        name=payload.name,
        description=payload.description,
    )


@router.put("/{topic_id}", response_model=TopicSummaryResponse)
async def update_topic(
    topic_id: int,
    payload: TopicUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    return await _call_topic_service(
        TopicService(db).update_topic,
        tenant_id=_current_user.tenant_id,
        topic_id=topic_id,
        name=payload.name,
        description=payload.description,
    )


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    await _call_topic_service(
        TopicService(db).delete_topic,
        tenant_id=_current_user.tenant_id,
        topic_id=topic_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/questions", response_model=QuestionPageResponse)
async def list_questions(
    topic_id: int | None = None,
    question_type: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await _call_topic_service(
        TopicService(db).list_questions_page,
        tenant_id=_current_user.tenant_id,
        limit=pagination.limit,
        offset=pagination.offset,
        topic_id=topic_id,
        question_type=question_type,
        search=search,
    )


@router.get("/prerequisites", response_model=TopicPrerequisitePageResponse)
async def list_prerequisites(
    topic_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await _call_topic_service(
        TopicService(db).list_prerequisites_page,
        tenant_id=_current_user.tenant_id,
        limit=pagination.limit,
        offset=pagination.offset,
        topic_id=topic_id,
    )


@router.post("/prerequisites", response_model=TopicPrerequisiteResponse)
async def create_prerequisite(
    payload: TopicPrerequisiteCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    return await _call_topic_service(
        TopicService(db).create_prerequisite,
        tenant_id=_current_user.tenant_id,
        topic_id=payload.topic_id,
        prerequisite_topic_id=payload.prerequisite_topic_id,
    )


@router.delete("/prerequisites/{prerequisite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prerequisite(
    prerequisite_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    await _call_topic_service(
        TopicService(db).delete_prerequisite,
        tenant_id=_current_user.tenant_id,
        prerequisite_id=prerequisite_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/questions", response_model=QuestionResponse)
async def create_question(
    payload: QuestionCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    return await TopicService(db).create_question(
        topic_id=payload.topic_id,
        difficulty=payload.difficulty,
        question_type=payload.question_type,
        question_text=payload.question_text,
        correct_answer=payload.correct_answer,
        accepted_answers=payload.accepted_answers,
        answer_options=payload.answer_options,
        tenant_id=_current_user.tenant_id,
    )


@router.post("/questions/import", response_model=QuestionImportResponse)
async def import_questions(
    payload: QuestionImportRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    created = await _call_topic_service(
        TopicService(db).import_questions,
        tenant_id=_current_user.tenant_id,
        items=[item.model_dump() for item in payload.items],
    )
    return QuestionImportResponse(created=created)


@router.post("/questions/import.csv", response_model=QuestionImportResponse)
async def import_questions_csv(
    content: str = Body(..., media_type="text/csv"),
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    created = await _call_topic_service(
        TopicService(db).import_questions_csv,
        tenant_id=_current_user.tenant_id,
        content=content,
    )
    return QuestionImportResponse(created=created)


@router.get("/questions/export", response_class=PlainTextResponse)
async def export_questions(
    topic_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(get_current_user),
):
    items = await _call_topic_service(
        TopicService(db).export_questions,
        tenant_id=_current_user.tenant_id,
        topic_id=topic_id,
    )
    return PlainTextResponse(
        content=json.dumps(items, indent=2),
        headers={"Content-Disposition": "attachment; filename=questions-export.json"},
    )


@router.get("/questions/export.csv", response_class=PlainTextResponse)
async def export_questions_csv(
    topic_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(get_current_user),
):
    content = await _call_topic_service(
        TopicService(db).export_questions_csv,
        tenant_id=_current_user.tenant_id,
        topic_id=topic_id,
    )
    return PlainTextResponse(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=questions-export.csv"},
    )


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    payload: QuestionUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    return await _call_topic_service(
        TopicService(db).update_question,
        tenant_id=_current_user.tenant_id,
        question_id=question_id,
        **payload.model_dump(),
    )


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    await _call_topic_service(
        TopicService(db).delete_question,
        tenant_id=_current_user.tenant_id,
        question_id=question_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{topic_id}", response_model=TopicDetailResponse)
async def get_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(get_current_user),
):
    return await TopicService(db).get_topic_detail(topic_id, tenant_id=_current_user.tenant_id)


@router.post("/ai/explain", response_model=TopicExplanationResponse)
async def explain_topic_with_ai(
    payload: TopicExplanationRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(get_current_user),
):
    return await TopicService(db).explain_topic(
        tenant_id=_current_user.tenant_id,
        user_id=_current_user.id,
        topic_name=payload.topic_name,
    )


@router.post("/questions/ai-generate", response_model=AIQuestionGenerationResponse)
async def generate_questions_with_ai(
    payload: AIQuestionGenerationRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    return await TopicService(db).generate_ai_questions(
        tenant_id=_current_user.tenant_id,
        user_id=_current_user.id,
        topic=payload.topic,
        difficulty=payload.difficulty,
        count=payload.count,
    )
