from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.badge import Badge
from app.domain.models.community import Community
from app.domain.models.community_member import CommunityMember
from app.domain.models.discussion_reply import DiscussionReply
from app.domain.models.discussion_thread import DiscussionThread
from app.domain.models.topic import Topic


class CommunityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_topic(self, topic_id: int, tenant_id: int | None = None) -> Topic | None:
        stmt = select(Topic).where(Topic.id == topic_id)
        if tenant_id is not None:
            stmt = stmt.where(Topic.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_communities(
        self,
        tenant_id: int,
        limit: int,
        offset: int,
        topic_id: int | None = None,
    ) -> list[Community]:
        stmt = select(Community).where(Community.tenant_id == tenant_id).order_by(Community.id.asc())
        if topic_id is not None:
            stmt = stmt.where(Community.topic_id == topic_id)
        result = await self.session.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def count_communities(self, tenant_id: int, topic_id: int | None = None) -> int:
        stmt = select(func.count(Community.id)).where(Community.tenant_id == tenant_id)
        if topic_id is not None:
            stmt = stmt.where(Community.topic_id == topic_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def get_community(self, tenant_id: int, community_id: int) -> Community | None:
        result = await self.session.execute(
            select(Community).where(Community.tenant_id == tenant_id, Community.id == community_id)
        )
        return result.scalar_one_or_none()

    async def get_community_by_topic(self, tenant_id: int, topic_id: int) -> Community | None:
        result = await self.session.execute(
            select(Community).where(Community.tenant_id == tenant_id, Community.topic_id == topic_id)
        )
        return result.scalar_one_or_none()

    async def create_community(
        self,
        tenant_id: int,
        topic_id: int,
        name: str,
        description: str,
    ) -> Community:
        community = Community(
            tenant_id=tenant_id,
            topic_id=topic_id,
            name=name,
            description=description,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(community)
        await self.session.flush()
        return community

    async def delete_community(self, community: Community) -> None:
        await self.session.delete(community)

    async def list_members(
        self,
        tenant_id: int,
        limit: int,
        offset: int,
        community_id: int | None = None,
    ) -> list[CommunityMember]:
        stmt = select(CommunityMember).where(CommunityMember.tenant_id == tenant_id).order_by(CommunityMember.id.asc())
        if community_id is not None:
            stmt = stmt.where(CommunityMember.community_id == community_id)
        result = await self.session.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def count_members(self, tenant_id: int, community_id: int | None = None) -> int:
        stmt = select(func.count(CommunityMember.id)).where(CommunityMember.tenant_id == tenant_id)
        if community_id is not None:
            stmt = stmt.where(CommunityMember.community_id == community_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def get_member(
        self,
        tenant_id: int,
        community_id: int,
        user_id: int,
    ) -> CommunityMember | None:
        result = await self.session.execute(
            select(CommunityMember).where(
                CommunityMember.tenant_id == tenant_id,
                CommunityMember.community_id == community_id,
                CommunityMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_member(
        self,
        tenant_id: int,
        community_id: int,
        user_id: int,
        role: str,
    ) -> CommunityMember:
        member = CommunityMember(
            tenant_id=tenant_id,
            community_id=community_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.now(timezone.utc),
        )
        self.session.add(member)
        await self.session.flush()
        return member

    async def list_threads(
        self,
        tenant_id: int,
        limit: int,
        offset: int,
        community_id: int | None = None,
    ) -> list[DiscussionThread]:
        stmt = select(DiscussionThread).where(DiscussionThread.tenant_id == tenant_id).order_by(
            DiscussionThread.created_at.desc(),
            DiscussionThread.id.desc(),
        )
        if community_id is not None:
            stmt = stmt.where(DiscussionThread.community_id == community_id)
        result = await self.session.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def count_threads(self, tenant_id: int, community_id: int | None = None) -> int:
        stmt = select(func.count(DiscussionThread.id)).where(DiscussionThread.tenant_id == tenant_id)
        if community_id is not None:
            stmt = stmt.where(DiscussionThread.community_id == community_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create_thread(
        self,
        tenant_id: int,
        community_id: int,
        author_user_id: int,
        title: str,
        body: str,
    ) -> DiscussionThread:
        thread = DiscussionThread(
            tenant_id=tenant_id,
            community_id=community_id,
            author_user_id=author_user_id,
            title=title,
            body=body,
            is_resolved=False,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(thread)
        await self.session.flush()
        return thread

    async def get_thread(self, tenant_id: int, thread_id: int) -> DiscussionThread | None:
        result = await self.session.execute(
            select(DiscussionThread).where(
                DiscussionThread.tenant_id == tenant_id,
                DiscussionThread.id == thread_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_thread_resolution(self, thread: DiscussionThread, is_resolved: bool) -> DiscussionThread:
        thread.is_resolved = is_resolved
        await self.session.flush()
        return thread

    async def list_replies(
        self,
        tenant_id: int,
        thread_id: int,
        limit: int,
        offset: int,
    ) -> list[DiscussionReply]:
        stmt = (
            select(DiscussionReply)
            .where(DiscussionReply.tenant_id == tenant_id, DiscussionReply.thread_id == thread_id)
            .order_by(DiscussionReply.created_at.asc(), DiscussionReply.id.asc())
        )
        result = await self.session.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def count_replies(self, tenant_id: int, thread_id: int) -> int:
        stmt = select(func.count(DiscussionReply.id)).where(
            DiscussionReply.tenant_id == tenant_id,
            DiscussionReply.thread_id == thread_id,
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create_reply(
        self,
        *,
        tenant_id: int,
        thread_id: int,
        author_user_id: int,
        body: str,
    ) -> DiscussionReply:
        reply = DiscussionReply(
            tenant_id=tenant_id,
            thread_id=thread_id,
            author_user_id=author_user_id,
            body=body,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(reply)
        await self.session.flush()
        return reply

    async def list_badges(
        self,
        tenant_id: int,
        limit: int,
        offset: int,
        user_id: int | None = None,
    ) -> list[Badge]:
        stmt = select(Badge).where(Badge.tenant_id == tenant_id).order_by(Badge.awarded_at.desc(), Badge.id.desc())
        if user_id is not None:
            stmt = stmt.where(Badge.user_id == user_id)
        result = await self.session.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def count_badges(self, tenant_id: int, user_id: int | None = None) -> int:
        stmt = select(func.count(Badge.id)).where(Badge.tenant_id == tenant_id)
        if user_id is not None:
            stmt = stmt.where(Badge.user_id == user_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create_badge(
        self,
        tenant_id: int,
        user_id: int,
        name: str,
        description: str,
        awarded_for: str,
    ) -> Badge:
        badge = Badge(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            description=description,
            awarded_for=awarded_for,
            awarded_at=datetime.now(timezone.utc),
        )
        self.session.add(badge)
        await self.session.flush()
        return badge

    async def get_badge(self, tenant_id: int, badge_id: int) -> Badge | None:
        result = await self.session.execute(
            select(Badge).where(Badge.tenant_id == tenant_id, Badge.id == badge_id)
        )
        return result.scalar_one_or_none()

    async def delete_badge(self, badge: Badge) -> None:
        await self.session.delete(badge)

    async def count_members_for_communities(self, tenant_id: int, community_ids: list[int]) -> dict[int, int]:
        if not community_ids:
            return {}
        result = await self.session.execute(
            select(CommunityMember.community_id, func.count(CommunityMember.id))
            .where(
                CommunityMember.tenant_id == tenant_id,
                CommunityMember.community_id.in_(community_ids),
            )
            .group_by(CommunityMember.community_id)
        )
        return {int(community_id): int(count) for community_id, count in result.all()}

    async def count_threads_for_communities(self, tenant_id: int, community_ids: list[int]) -> dict[int, int]:
        if not community_ids:
            return {}
        result = await self.session.execute(
            select(DiscussionThread.community_id, func.count(DiscussionThread.id))
            .where(
                DiscussionThread.tenant_id == tenant_id,
                DiscussionThread.community_id.in_(community_ids),
            )
            .group_by(DiscussionThread.community_id)
        )
        return {int(community_id): int(count) for community_id, count in result.all()}

    async def list_membership_community_ids(self, tenant_id: int, user_id: int) -> set[int]:
        result = await self.session.execute(
            select(CommunityMember.community_id).where(
                CommunityMember.tenant_id == tenant_id,
                CommunityMember.user_id == user_id,
            )
        )
        return {int(community_id) for community_id in result.scalars().all()}
