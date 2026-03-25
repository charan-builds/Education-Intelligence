from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.social_network_service import SocialNetworkService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.schemas.social_schema import SocialFollowRequest, SocialNetworkResponse

router = APIRouter(prefix="/social", tags=["social"])


@router.get("/network", response_model=SocialNetworkResponse)
async def get_social_network(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await SocialNetworkService(db).get_network(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )


@router.post("/follows", status_code=status.HTTP_204_NO_CONTENT)
async def follow_user(
    payload: SocialFollowRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    await SocialNetworkService(db).follow(
        tenant_id=current_user.tenant_id,
        follower_user_id=current_user.id,
        followed_user_id=payload.user_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/follows/{followed_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    followed_user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    await SocialNetworkService(db).unfollow(
        tenant_id=current_user.tenant_id,
        follower_user_id=current_user.id,
        followed_user_id=followed_user_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
