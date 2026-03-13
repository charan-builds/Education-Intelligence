from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.goal_service import GoalService
from app.core.dependencies import get_current_user, get_pagination_params
from app.infrastructure.database import get_db_session
from app.schemas.common_schema import PaginationParams
from app.schemas.goal_schema import GoalPageResponse

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=GoalPageResponse)
async def list_goals(
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await GoalService(db).list_goals_page(
        limit=pagination.limit,
        offset=pagination.offset,
        cursor=pagination.cursor,
    )
