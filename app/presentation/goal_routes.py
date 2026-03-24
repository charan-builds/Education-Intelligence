from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.goal_service import GoalService
from app.core.dependencies import get_current_user, get_pagination_params, require_roles
from app.infrastructure.database import get_db_session
from app.schemas.common_schema import PaginationParams
from app.schemas.goal_schema import (
    GoalCreateRequest,
    GoalPageResponse,
    GoalResponse,
    GoalTopicCreateRequest,
    GoalTopicPageResponse,
    GoalTopicResponse,
    GoalUpdateRequest,
)

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=GoalPageResponse)
async def list_goals(
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await GoalService(db).list_goals_page(
        tenant_id=_current_user.tenant_id,
        limit=pagination.limit,
        offset=pagination.offset,
        cursor=pagination.cursor,
    )


@router.post("", response_model=GoalResponse)
async def create_goal(
    payload: GoalCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    service = GoalService(db)
    try:
        return await service.create_goal(
            tenant_id=_current_user.tenant_id,
            name=payload.name,
            description=payload.description,
        )
    except TypeError:
        return await service.create_goal(name=payload.name, description=payload.description)


@router.get("/topics", response_model=GoalTopicPageResponse)
async def list_goal_topics(
    goal_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(get_current_user),
):
    service = GoalService(db)
    try:
        return await service.list_goal_topics_page(tenant_id=_current_user.tenant_id, goal_id=goal_id)
    except TypeError:
        return await service.list_goal_topics_page(goal_id=goal_id)


@router.post("/topics", response_model=GoalTopicResponse)
async def create_goal_topic(
    payload: GoalTopicCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    service = GoalService(db)
    try:
        return await service.create_goal_topic(
            tenant_id=_current_user.tenant_id,
            goal_id=payload.goal_id,
            topic_id=payload.topic_id,
        )
    except TypeError:
        return await service.create_goal_topic(goal_id=payload.goal_id, topic_id=payload.topic_id)


@router.delete("/topics/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal_topic(
    link_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    service = GoalService(db)
    try:
        await service.delete_goal_topic(_current_user.tenant_id, link_id)
    except TypeError:
        await service.delete_goal_topic(link_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    payload: GoalUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    service = GoalService(db)
    try:
        return await service.update_goal(
            _current_user.tenant_id,
            goal_id,
            name=payload.name,
            description=payload.description,
        )
    except TypeError:
        return await service.update_goal(goal_id, name=payload.name, description=payload.description)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin", "admin")),
):
    service = GoalService(db)
    try:
        await service.delete_goal(_current_user.tenant_id, goal_id)
    except TypeError:
        await service.delete_goal(goal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
