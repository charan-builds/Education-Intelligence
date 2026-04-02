from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ai_chat_service import AIChatService
from app.application.services.ai_request_service import AIRequestService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.schemas.ai_schema import AIChatRequest, AIChatResponse, AIChatHistoryItemResponse, AIRequestStatusResponse

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/chat", response_model=list[AIChatHistoryItemResponse])
async def ai_chat_history(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await AIChatService(db).history(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    payload: AIChatRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await AIChatService(db).chat(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        message=payload.message,
        chat_history=payload.chat_history,
    )


@router.get("/requests/{request_id}", response_model=AIRequestStatusResponse)
async def ai_request_status(
    request_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    from fastapi import HTTPException, status

    result = await AIRequestService(db).get_result(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        request_id=request_id,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI request not found")
    status_value = str(result.get("status") or "unknown")
    response_payload = dict(result)
    response_payload["meta"] = {
        "is_pending": status_value in {"queued", "processing"},
        "is_terminal": status_value in {"completed", "failed", "timed_out", "fallback"},
        "has_error": bool(result.get("error_message")),
    }
    return AIRequestStatusResponse(**response_payload)
