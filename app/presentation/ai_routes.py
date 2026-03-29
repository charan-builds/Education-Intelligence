from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ai_chat_service import AIChatService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.schemas.ai_schema import AIChatRequest, AIChatResponse, AIChatHistoryItemResponse

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
