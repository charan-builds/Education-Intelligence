from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.goal_service import GoalService
from app.core.dependencies import get_current_user, require_profile_completed
from app.infrastructure.database import get_db_session
from app.schemas.goal_schema import UserGoalResponse, UserGoalSelectRequest

router = APIRouter(prefix="/user/goals", tags=["user-goals"])


@router.post("/select", response_model=UserGoalResponse)
async def select_user_goal(
    payload: UserGoalSelectRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_profile_completed),
):
    return await GoalService(db).select_goal_for_user(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        goal_id=payload.goal_id,
    )


@router.get("/current", response_model=UserGoalResponse | None)
async def get_current_user_goal(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await GoalService(db).get_current_goal_for_user(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
