from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.community_service import CommunityService
from app.core.dependencies import get_current_user, get_pagination_params, require_roles
from app.infrastructure.database import get_db_session
from app.realtime.hub import realtime_hub
from app.schemas.common_schema import PaginationParams
from app.schemas.community_schema import (
    BadgeResponse,
    BadgePageResponse,
    BadgeCreateRequest,
    CommunityCreateRequest,
    CommunityMemberCreateRequest,
    CommunityMemberPageResponse,
    CommunityMemberResponse,
    CommunityPageResponse,
    CommunityResponse,
    DiscussionReplyCreateRequest,
    DiscussionReplyPageResponse,
    DiscussionReplyResponse,
    DiscussionThreadCreateRequest,
    DiscussionThreadPageResponse,
    DiscussionThreadResolveRequest,
    DiscussionThreadResponse,
)

router = APIRouter(prefix="/community", tags=["community"])


@router.get("/communities", response_model=CommunityPageResponse)
async def list_communities(
    topic_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await CommunityService(db).list_communities_page(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        limit=pagination.limit,
        offset=pagination.offset,
        topic_id=topic_id,
    )


@router.post("/communities", response_model=CommunityResponse)
async def create_community(
    payload: CommunityCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    return await CommunityService(db).create_community(
        tenant_id=current_user.tenant_id,
        topic_id=payload.topic_id,
        name=payload.name,
        description=payload.description,
    )


@router.delete("/communities/{community_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_community(
    community_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    await CommunityService(db).delete_community(
        tenant_id=current_user.tenant_id,
        community_id=community_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/members", response_model=CommunityMemberPageResponse)
async def list_members(
    community_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await CommunityService(db).list_members_page(
        tenant_id=current_user.tenant_id,
        limit=pagination.limit,
        offset=pagination.offset,
        community_id=community_id,
    )


@router.post("/members", response_model=CommunityMemberResponse)
async def join_community(
    payload: CommunityMemberCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await CommunityService(db).join_community(
        tenant_id=current_user.tenant_id,
        community_id=payload.community_id,
        user_id=current_user.id,
        role=current_user.role.value,
    )


@router.get("/threads", response_model=DiscussionThreadPageResponse)
async def list_threads(
    community_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await CommunityService(db).list_threads_page(
        tenant_id=current_user.tenant_id,
        limit=pagination.limit,
        offset=pagination.offset,
        community_id=community_id,
    )


@router.post("/threads", response_model=DiscussionThreadResponse)
async def create_thread(
    payload: DiscussionThreadCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    result = await CommunityService(db).create_thread(
        tenant_id=current_user.tenant_id,
        community_id=payload.community_id,
        author_user_id=current_user.id,
        author_role=current_user.role.value,
        title=payload.title,
        body=payload.body,
    )
    await realtime_hub.send_community(
        current_user.tenant_id,
        payload.community_id,
        {"type": "community.thread.created", "thread": result},
    )
    await realtime_hub.send_tenant(
        current_user.tenant_id,
        {
            "type": "activity.created",
            "scope": "tenant",
            "event_type": "discussion_thread_created",
            "user_id": current_user.id,
            "community_id": payload.community_id,
            "message": f"New discussion thread posted in community {payload.community_id}.",
        },
    )
    return result


@router.get("/replies", response_model=DiscussionReplyPageResponse)
async def list_replies(
    thread_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await CommunityService(db).list_replies_page(
        tenant_id=current_user.tenant_id,
        thread_id=thread_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post("/replies", response_model=DiscussionReplyResponse)
async def create_reply(
    payload: DiscussionReplyCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    result = await CommunityService(db).create_reply(
        tenant_id=current_user.tenant_id,
        thread_id=payload.thread_id,
        author_user_id=current_user.id,
        author_role=current_user.role.value,
        body=payload.body,
    )
    await realtime_hub.send_thread(
        current_user.tenant_id,
        payload.thread_id,
        {"type": "community.reply.created", "reply": result},
    )
    await realtime_hub.send_tenant(
        current_user.tenant_id,
        {
            "type": "activity.created",
            "scope": "tenant",
            "event_type": "discussion_reply_created",
            "user_id": current_user.id,
            "thread_id": payload.thread_id,
            "message": f"New reply posted in thread {payload.thread_id}.",
        },
    )
    return result


@router.patch("/threads/{thread_id}/resolve", response_model=DiscussionThreadResponse)
async def resolve_thread(
    thread_id: int,
    payload: DiscussionThreadResolveRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "admin", "super_admin")),
):
    return await CommunityService(db).resolve_thread(
        tenant_id=current_user.tenant_id,
        thread_id=thread_id,
        is_resolved=payload.is_resolved,
    )


@router.get("/badges", response_model=BadgePageResponse)
async def list_badges(
    user_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await CommunityService(db).list_badges_page(
        tenant_id=current_user.tenant_id,
        limit=pagination.limit,
        offset=pagination.offset,
        user_id=user_id,
    )


@router.post("/badges", response_model=BadgeResponse)
async def award_badge(
    payload: BadgeCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    return await CommunityService(db).award_badge(
        tenant_id=current_user.tenant_id,
        user_id=payload.user_id,
        name=payload.name,
        description=payload.description,
        awarded_for=payload.awarded_for,
    )


@router.delete("/badges/{badge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_badge(
    badge_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    await CommunityService(db).revoke_badge(
        tenant_id=current_user.tenant_id,
        badge_id=badge_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
