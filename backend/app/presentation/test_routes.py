from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.test_generator_service import SmartTestGeneratorService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.schemas.test_generation_schema import SmartTestGenerateRequest, SmartTestGenerateResponse

router = APIRouter(prefix="/test", tags=["test"])


@router.post("/generate-smart", response_model=SmartTestGenerateResponse)
async def generate_smart_test(
    payload: SmartTestGenerateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await SmartTestGeneratorService(db).generate_smart_test(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        goal_id=payload.goal_id,
        question_count=payload.question_count,
    )
