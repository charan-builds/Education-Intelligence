from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.infrastructure.repositories.community_repository import CommunityRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.infrastructure.repositories.user_repository import UserRepository


class CommunityService:
    def __init__(self, session: AsyncSession):
        self.repository = CommunityRepository(session)
        self.topic_repository = TopicRepository(session)
        self.user_repository = UserRepository(session)

    async def _user_email_lookup(self, tenant_id: int, user_ids: set[int]) -> dict[int, str]:
        users = await self.user_repository.get_by_ids_in_tenant(sorted(user_ids), tenant_id)
        return {int(user.id): user.email for user in users}

    async def list_communities_page(
        self,
        *,
        tenant_id: int,
        user_id: int,
        limit: int,
        offset: int,
        topic_id: int | None = None,
    ) -> dict:
        items = await self.repository.list_communities(tenant_id=tenant_id, limit=limit, offset=offset, topic_id=topic_id)
        total = await self.repository.count_communities(tenant_id=tenant_id, topic_id=topic_id)
        next_offset = offset + limit if (offset + limit) < total else None

        topic_lookup = {
            topic.id: topic.name
            for topic in await self.topic_repository.list_topics_by_ids(
                [item.topic_id for item in items],
                tenant_id=tenant_id,
            )
        }
        member_counts = await self.repository.count_members_for_communities(tenant_id, [item.id for item in items])
        thread_counts = await self.repository.count_threads_for_communities(tenant_id, [item.id for item in items])
        membership_ids = await self.repository.list_membership_community_ids(tenant_id, user_id)

        return {
            "items": [
                {
                    "id": item.id,
                    "tenant_id": item.tenant_id,
                    "topic_id": item.topic_id,
                    "name": item.name,
                    "description": item.description,
                    "created_at": item.created_at,
                    "topic_name": topic_lookup.get(item.topic_id),
                    "member_count": member_counts.get(item.id, 0),
                    "thread_count": thread_counts.get(item.id, 0),
                    "is_member": item.id in membership_ids,
                }
                for item in items
            ],
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": None,
            },
        }

    async def create_community(
        self,
        *,
        tenant_id: int,
        topic_id: int,
        name: str,
        description: str,
    ):
        topic = await self.repository.get_topic(topic_id, tenant_id=tenant_id)
        if topic is None:
            raise NotFoundError("Topic not found")
        if await self.repository.get_community_by_topic(tenant_id, topic_id) is not None:
            raise ConflictError("Community already exists for this topic")
        community = await self.repository.create_community(
            tenant_id=tenant_id,
            topic_id=topic_id,
            name=name.strip(),
            description=description.strip(),
        )
        await self.repository.session.commit()
        return {
            "id": community.id,
            "tenant_id": community.tenant_id,
            "topic_id": community.topic_id,
            "name": community.name,
            "description": community.description,
            "created_at": community.created_at,
            "topic_name": topic.name,
            "member_count": 0,
            "thread_count": 0,
            "is_member": False,
        }

    async def delete_community(self, *, tenant_id: int, community_id: int) -> None:
        community = await self.repository.get_community(tenant_id, community_id)
        if community is None:
            raise NotFoundError("Community not found")
        await self.repository.delete_community(community)
        await self.repository.session.commit()

    async def list_members_page(
        self,
        *,
        tenant_id: int,
        limit: int,
        offset: int,
        community_id: int | None = None,
    ) -> dict:
        items = await self.repository.list_members(tenant_id=tenant_id, limit=limit, offset=offset, community_id=community_id)
        total = await self.repository.count_members(tenant_id=tenant_id, community_id=community_id)
        next_offset = offset + limit if (offset + limit) < total else None
        user_lookup = await self._user_email_lookup(tenant_id, {int(item.user_id) for item in items})
        return {
            "items": [
                {
                    "id": item.id,
                    "tenant_id": item.tenant_id,
                    "community_id": item.community_id,
                    "user_id": item.user_id,
                    "role": item.role,
                    "joined_at": item.joined_at,
                    "user_email": user_lookup.get(item.user_id),
                }
                for item in items
            ],
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": None,
            },
        }

    async def join_community(self, *, tenant_id: int, community_id: int, user_id: int, role: str):
        community = await self.repository.get_community(tenant_id, community_id)
        if community is None:
            raise NotFoundError("Community not found")
        if await self.repository.get_member(tenant_id, community_id, user_id) is not None:
            raise ConflictError("User already joined this community")

        member = await self.repository.create_member(
            tenant_id=tenant_id,
            community_id=community_id,
            user_id=user_id,
            role=role,
        )
        await self.repository.session.commit()
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        return {
            "id": member.id,
            "tenant_id": member.tenant_id,
            "community_id": member.community_id,
            "user_id": member.user_id,
            "role": member.role,
            "joined_at": member.joined_at,
            "user_email": user.email if user else None,
        }

    async def list_threads_page(
        self,
        *,
        tenant_id: int,
        limit: int,
        offset: int,
        community_id: int | None = None,
    ) -> dict:
        items = await self.repository.list_threads(tenant_id=tenant_id, limit=limit, offset=offset, community_id=community_id)
        total = await self.repository.count_threads(tenant_id=tenant_id, community_id=community_id)
        next_offset = offset + limit if (offset + limit) < total else None

        community_lookup = {
            community.id: community.name
            for community in await self.repository.list_communities(tenant_id=tenant_id, limit=100, offset=0)
        }
        user_lookup = await self._user_email_lookup(tenant_id, {int(item.author_user_id) for item in items})
        return {
            "items": [
                {
                    "id": item.id,
                    "tenant_id": item.tenant_id,
                    "community_id": item.community_id,
                    "author_user_id": item.author_user_id,
                    "title": item.title,
                    "body": item.body,
                    "is_resolved": item.is_resolved,
                    "created_at": item.created_at,
                    "author_email": user_lookup.get(item.author_user_id),
                    "community_name": community_lookup.get(item.community_id),
                }
                for item in items
            ],
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": None,
            },
        }

    async def create_thread(
        self,
        *,
        tenant_id: int,
        community_id: int,
        author_user_id: int,
        author_role: str,
        title: str,
        body: str,
    ):
        community = await self.repository.get_community(tenant_id, community_id)
        if community is None:
            raise NotFoundError("Community not found")

        membership = await self.repository.get_member(tenant_id, community_id, author_user_id)
        privileged_roles = {"teacher", "admin", "super_admin"}
        if membership is None and author_role not in privileged_roles:
            raise UnauthorizedError("Join the community before posting a thread")

        thread = await self.repository.create_thread(
            tenant_id=tenant_id,
            community_id=community_id,
            author_user_id=author_user_id,
            title=title.strip(),
            body=body.strip(),
        )
        await self.repository.session.commit()
        author = await self.user_repository.get_by_id_in_tenant(author_user_id, tenant_id)
        return {
            "id": thread.id,
            "tenant_id": thread.tenant_id,
            "community_id": thread.community_id,
            "author_user_id": thread.author_user_id,
            "title": thread.title,
            "body": thread.body,
            "is_resolved": thread.is_resolved,
            "created_at": thread.created_at,
            "author_email": author.email if author else None,
            "community_name": community.name,
        }

    async def resolve_thread(
        self,
        *,
        tenant_id: int,
        thread_id: int,
        is_resolved: bool,
    ) -> dict:
        thread = await self.repository.get_thread(tenant_id, thread_id)
        if thread is None:
            raise NotFoundError("Discussion thread not found")

        updated = await self.repository.update_thread_resolution(thread, is_resolved)
        await self.repository.session.commit()
        author = await self.user_repository.get_by_id_in_tenant(updated.author_user_id, tenant_id)
        community = await self.repository.get_community(tenant_id, updated.community_id)
        return {
            "id": updated.id,
            "tenant_id": updated.tenant_id,
            "community_id": updated.community_id,
            "author_user_id": updated.author_user_id,
            "title": updated.title,
            "body": updated.body,
            "is_resolved": updated.is_resolved,
            "created_at": updated.created_at,
            "author_email": author.email if author else None,
            "community_name": community.name if community else None,
        }

    async def list_replies_page(
        self,
        *,
        tenant_id: int,
        thread_id: int,
        limit: int,
        offset: int,
    ) -> dict:
        thread = await self.repository.get_thread(tenant_id, thread_id)
        if thread is None:
            raise NotFoundError("Discussion thread not found")

        items = await self.repository.list_replies(
            tenant_id=tenant_id,
            thread_id=thread_id,
            limit=limit,
            offset=offset,
        )
        total = await self.repository.count_replies(tenant_id=tenant_id, thread_id=thread_id)
        next_offset = offset + limit if (offset + limit) < total else None
        author_lookup = await self._user_email_lookup(tenant_id, {int(item.author_user_id) for item in items})
        return {
            "items": [
                {
                    "id": item.id,
                    "tenant_id": item.tenant_id,
                    "thread_id": item.thread_id,
                    "author_user_id": item.author_user_id,
                    "body": item.body,
                    "created_at": item.created_at,
                    "author_email": author_lookup.get(item.author_user_id),
                }
                for item in items
            ],
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": None,
            },
        }

    async def create_reply(
        self,
        *,
        tenant_id: int,
        thread_id: int,
        author_user_id: int,
        author_role: str,
        body: str,
    ) -> dict:
        thread = await self.repository.get_thread(tenant_id, thread_id)
        if thread is None:
            raise NotFoundError("Discussion thread not found")

        membership = await self.repository.get_member(tenant_id, thread.community_id, author_user_id)
        privileged_roles = {"teacher", "admin", "super_admin"}
        if membership is None and author_role not in privileged_roles:
            raise UnauthorizedError("Join the community before replying")

        reply = await self.repository.create_reply(
            tenant_id=tenant_id,
            thread_id=thread_id,
            author_user_id=author_user_id,
            body=body.strip(),
        )
        await self.repository.session.commit()
        author = await self.user_repository.get_by_id_in_tenant(author_user_id, tenant_id)
        return {
            "id": reply.id,
            "tenant_id": reply.tenant_id,
            "thread_id": reply.thread_id,
            "author_user_id": reply.author_user_id,
            "body": reply.body,
            "created_at": reply.created_at,
            "author_email": author.email if author else None,
        }

    async def list_badges_page(
        self,
        *,
        tenant_id: int,
        limit: int,
        offset: int,
        user_id: int | None = None,
    ) -> dict:
        items = await self.repository.list_badges(tenant_id=tenant_id, limit=limit, offset=offset, user_id=user_id)
        total = await self.repository.count_badges(tenant_id=tenant_id, user_id=user_id)
        next_offset = offset + limit if (offset + limit) < total else None
        user_lookup = await self._user_email_lookup(tenant_id, {int(item.user_id) for item in items})
        return {
            "items": [
                {
                    "id": item.id,
                    "tenant_id": item.tenant_id,
                    "user_id": item.user_id,
                    "name": item.name,
                    "description": item.description,
                    "awarded_for": item.awarded_for,
                    "awarded_at": item.awarded_at,
                    "user_email": user_lookup.get(item.user_id),
                }
                for item in items
            ],
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": None,
            },
        }

    async def award_badge(
        self,
        *,
        tenant_id: int,
        user_id: int,
        name: str,
        description: str,
        awarded_for: str,
    ) -> dict:
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise NotFoundError("User not found")

        badge = await self.repository.create_badge(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name.strip(),
            description=description.strip(),
            awarded_for=awarded_for.strip() or "mentorship",
        )
        await self.repository.session.commit()
        return {
            "id": badge.id,
            "tenant_id": badge.tenant_id,
            "user_id": badge.user_id,
            "name": badge.name,
            "description": badge.description,
            "awarded_for": badge.awarded_for,
            "awarded_at": badge.awarded_at,
            "user_email": user.email,
        }

    async def revoke_badge(self, *, tenant_id: int, badge_id: int) -> None:
        badge = await self.repository.get_badge(tenant_id, badge_id)
        if badge is None:
            raise NotFoundError("Badge not found")
        await self.repository.delete_badge(badge)
        await self.repository.session.commit()
