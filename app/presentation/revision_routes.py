from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.retention_service import RetentionService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.schemas.revision_schema import RevisionTodayResponse

router = APIRouter(prefix="/revision", tags=["revision"])


@router.get("/today", response_model=RevisionTodayResponse)
async def revision_today(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await RetentionService(db).revisions_due_today(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
