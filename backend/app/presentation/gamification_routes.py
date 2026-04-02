from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.gamification_service import GamificationService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.schemas.gamification_schema import (
    GamificationEventItemResponse,
    GamificationProfileResponse,
    LeaderboardResponse,
)

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/me", response_model=GamificationProfileResponse)
async def gamification_me(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await GamificationService(db).get_profile(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def gamification_leaderboard(
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await GamificationService(db).get_leaderboard(
        tenant_id=current_user.tenant_id,
        current_user_id=current_user.id,
        limit=limit,
    )


@router.get("/activity", response_model=list[GamificationEventItemResponse])
async def gamification_activity(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await GamificationService(db).recent_activity(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        limit=limit,
    )
