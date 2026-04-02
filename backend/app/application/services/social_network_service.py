from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import ConflictError, NotFoundError
from app.domain.models.badge import Badge
from app.domain.models.community import Community
from app.domain.models.community_member import CommunityMember
from app.domain.models.learning_event import LearningEvent
from app.domain.models.roadmap import Roadmap
from app.domain.models.roadmap_step import RoadmapStep
from app.domain.models.social_follow import SocialFollow
from app.domain.models.topic import Topic
from app.domain.models.topic_score import TopicScore
from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.community_repository import CommunityRepository
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.repositories.tenant_scoping import user_belongs_to_tenant, user_has_tenant_role
from app.infrastructure.repositories.user_repository import UserRepository


class SocialNetworkService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repository = UserRepository(session)
        self.community_repository = CommunityRepository(session)
        self.roadmap_repository = RoadmapRepository(session)

    async def follow(self, *, tenant_id: int, follower_user_id: int, followed_user_id: int) -> None:
        if follower_user_id == followed_user_id:
            raise ConflictError("You cannot follow yourself")
        followed = await self.user_repository.get_by_id_in_tenant(followed_user_id, tenant_id)
        if followed is None:
            raise NotFoundError("User not found")
        existing = await self.session.execute(
            select(SocialFollow).where(
                SocialFollow.tenant_id == tenant_id,
                SocialFollow.follower_user_id == follower_user_id,
                SocialFollow.followed_user_id == followed_user_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("Already following this user")
        self.session.add(
            SocialFollow(
                tenant_id=tenant_id,
                follower_user_id=follower_user_id,
                followed_user_id=followed_user_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        await self.session.commit()

    async def unfollow(self, *, tenant_id: int, follower_user_id: int, followed_user_id: int) -> None:
        result = await self.session.execute(
            select(SocialFollow).where(
                SocialFollow.tenant_id == tenant_id,
                SocialFollow.follower_user_id == follower_user_id,
                SocialFollow.followed_user_id == followed_user_id,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise NotFoundError("Follow relationship not found")
        await self.session.delete(record)
        await self.session.commit()

    async def _topic_name_map(self, tenant_id: int) -> dict[int, str]:
        result = await self.session.execute(select(Topic.id, Topic.name).where(Topic.tenant_id == tenant_id))
        return {int(topic_id): str(name) for topic_id, name in result.all()}

    async def _roadmap_completion(self, tenant_id: int, user_ids: list[int]) -> dict[int, float]:
        if not user_ids:
            return {}
        latest_roadmap_ids = (
            select(Roadmap.user_id.label("user_id"), func.max(Roadmap.id).label("roadmap_id"))
            .where(Roadmap.user_id.in_(user_ids))
            .group_by(Roadmap.user_id)
            .subquery()
        )
        result = await self.session.execute(
            select(
                latest_roadmap_ids.c.user_id,
                func.count(RoadmapStep.id).label("total_steps"),
                func.coalesce(
                    func.sum(func.cast(RoadmapStep.progress_status == "completed", Integer)),
                    0,
                ).label("completed_steps"),
            )
            .select_from(latest_roadmap_ids)
            .join(User, User.id == latest_roadmap_ids.c.user_id)
            .outerjoin(RoadmapStep, RoadmapStep.roadmap_id == latest_roadmap_ids.c.roadmap_id)
            .where(user_belongs_to_tenant(User, tenant_id))
            .group_by(latest_roadmap_ids.c.user_id)
        )
        values = {int(user_id): 0.0 for user_id in user_ids}
        for user_id, total_steps, completed_steps in result.all():
            total = int(total_steps or 0)
            completed = int(completed_steps or 0)
            values[int(user_id)] = round((completed / total) * 100.0, 2) if total else 0.0
        return values

    async def _build_profiles(
        self,
        *,
        tenant_id: int,
        current_user_id: int,
        users: list[User],
        following_ids: set[int],
    ) -> list[dict]:
        if not users:
            return []
        user_ids = [int(user.id) for user in users]
        topic_names = await self._topic_name_map(tenant_id)
        completion = await self._roadmap_completion(tenant_id, user_ids)

        score_result = await self.session.execute(
            select(TopicScore).where(TopicScore.tenant_id == tenant_id, TopicScore.user_id.in_(user_ids))
        )
        scores_by_user: dict[int, list[TopicScore]] = defaultdict(list)
        for row in score_result.scalars().all():
            scores_by_user[int(row.user_id)].append(row)

        badge_result = await self.session.execute(
            select(Badge).where(Badge.tenant_id == tenant_id, Badge.user_id.in_(user_ids)).order_by(Badge.awarded_at.desc())
        )
        badges_by_user: dict[int, list[Badge]] = defaultdict(list)
        for badge in badge_result.scalars().all():
            badges_by_user[int(badge.user_id)].append(badge)

        member_result = await self.session.execute(
            select(CommunityMember, Community)
            .join(Community, Community.id == CommunityMember.community_id)
            .where(CommunityMember.tenant_id == tenant_id, CommunityMember.user_id.in_(user_ids))
        )
        communities_by_user: dict[int, list[str]] = defaultdict(list)
        for member, community in member_result.all():
            communities_by_user[int(member.user_id)].append(str(community.name))

        follower_counts_result = await self.session.execute(
            select(SocialFollow.followed_user_id, func.count(SocialFollow.id))
            .where(SocialFollow.tenant_id == tenant_id, SocialFollow.followed_user_id.in_(user_ids))
            .group_by(SocialFollow.followed_user_id)
        )
        follower_counts = {int(user_id): int(count) for user_id, count in follower_counts_result.all()}
        following_counts_result = await self.session.execute(
            select(SocialFollow.follower_user_id, func.count(SocialFollow.id))
            .where(SocialFollow.tenant_id == tenant_id, SocialFollow.follower_user_id.in_(user_ids))
            .group_by(SocialFollow.follower_user_id)
        )
        following_counts = {int(user_id): int(count) for user_id, count in following_counts_result.all()}

        profiles: list[dict] = []
        for user in users:
            score_rows = scores_by_user.get(int(user.id), [])
            strongest = sorted(score_rows, key=lambda item: float(item.score), reverse=True)[:3]
            weakest = sorted(score_rows, key=lambda item: float(item.score))[:3]
            display_name = user.display_name or user.email.split("@")[0].replace(".", " ").title()
            profiles.append(
                {
                    "user_id": int(user.id),
                    "display_name": display_name,
                    "email": user.email,
                    "role": user.role.value,
                    "xp": int(user.experience_points or 0),
                    "streak_days": int(user.current_streak_days or 0),
                    "completion_percent": completion.get(int(user.id), 0.0),
                    "top_skills": [topic_names.get(int(item.topic_id), f"Topic {item.topic_id}") for item in strongest],
                    "weak_topics": [topic_names.get(int(item.topic_id), f"Topic {item.topic_id}") for item in weakest if float(item.score) < 70.0],
                    "badges": [badge.name for badge in badges_by_user.get(int(user.id), [])[:3]],
                    "communities": communities_by_user.get(int(user.id), [])[:3],
                    "is_following": int(user.id) in following_ids if int(user.id) != current_user_id else False,
                    "follower_count": follower_counts.get(int(user.id), 0),
                    "following_count": following_counts.get(int(user.id), 0),
                    "tagline": (
                        f"{display_name} is at {completion.get(int(user.id), 0.0):.0f}% roadmap completion with "
                        f"{int(user.current_streak_days or 0)} day streak."
                    ),
                }
            )
        return profiles

    async def _build_feed(self, *, tenant_id: int, visible_user_ids: list[int]) -> list[dict]:
        if not visible_user_ids:
            return []
        events_result = await self.session.execute(
            select(LearningEvent, User)
            .join(User, User.id == LearningEvent.user_id)
            .where(LearningEvent.tenant_id == tenant_id, LearningEvent.user_id.in_(visible_user_ids))
            .order_by(LearningEvent.created_at.desc())
            .limit(12)
        )
        items: list[dict] = []
        for event, user in events_result.all():
            actor_name = user.display_name or user.email.split("@")[0].replace(".", " ").title()
            items.append(
                {
                    "actor_user_id": int(user.id),
                    "actor_name": actor_name,
                    "event_type": str(event.event_type),
                    "title": f"{actor_name} logged {str(event.event_type).replace('_', ' ')}",
                    "description": (
                        f"Shared progress on topic {event.topic_id}."
                        if event.topic_id is not None
                        else "Shared platform learning activity."
                    ),
                    "created_at": event.created_at,
                    "tone": "info",
                }
            )

        badge_result = await self.session.execute(
            select(Badge, User)
            .join(User, User.id == Badge.user_id)
            .where(Badge.tenant_id == tenant_id, Badge.user_id.in_(visible_user_ids))
            .order_by(Badge.awarded_at.desc())
            .limit(8)
        )
        for badge, user in badge_result.all():
            actor_name = user.display_name or user.email.split("@")[0].replace(".", " ").title()
            items.append(
                {
                    "actor_user_id": int(user.id),
                    "actor_name": actor_name,
                    "event_type": "badge_awarded",
                    "title": f"{actor_name} unlocked {badge.name}",
                    "description": badge.description,
                    "created_at": badge.awarded_at,
                    "tone": "success",
                }
            )
        items.sort(key=lambda item: item["created_at"], reverse=True)
        return items[:14]

    async def get_network(self, *, tenant_id: int, user_id: int) -> dict:
        me = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if me is None:
            raise NotFoundError("User not found")

        follow_rows = await self.session.execute(
            select(SocialFollow.followed_user_id).where(
                SocialFollow.tenant_id == tenant_id,
                SocialFollow.follower_user_id == user_id,
            )
        )
        following_ids = {int(item) for item in follow_rows.scalars().all()}

        network_users_result = await self.session.execute(
            select(User)
            .where(
                user_has_tenant_role(
                    User,
                    tenant_id,
                    UserRole.student.value,
                    UserRole.teacher.value,
                    UserRole.mentor.value,
                ),
                User.id != user_id,
            )
            .order_by(User.experience_points.desc(), User.id.asc())
            .limit(18)
        )
        network_users = list(network_users_result.scalars().all())
        following_users = [user for user in network_users if int(user.id) in following_ids]
        suggested_users = [user for user in network_users if int(user.id) not in following_ids][:6]

        me_profile = (await self._build_profiles(tenant_id=tenant_id, current_user_id=user_id, users=[me], following_ids=following_ids))[0]
        following_profiles = await self._build_profiles(
            tenant_id=tenant_id,
            current_user_id=user_id,
            users=following_users[:6],
            following_ids=following_ids,
        )
        suggested_profiles = await self._build_profiles(
            tenant_id=tenant_id,
            current_user_id=user_id,
            users=suggested_users,
            following_ids=following_ids,
        )

        visible_user_ids = [user_id, *[item["user_id"] for item in following_profiles], *[item["user_id"] for item in suggested_profiles[:3]]]
        feed = await self._build_feed(tenant_id=tenant_id, visible_user_ids=visible_user_ids)

        communities = await self.community_repository.list_communities(tenant_id=tenant_id, limit=6, offset=0)
        members_by_community: dict[int, list[User]] = defaultdict(list)
        if communities:
            group_members_result = await self.session.execute(
                select(CommunityMember, User)
                .join(User, User.id == CommunityMember.user_id)
                .where(
                    CommunityMember.tenant_id == tenant_id,
                    CommunityMember.community_id.in_([community.id for community in communities]),
                )
            )
            for member, user in group_members_result.all():
                members_by_community[int(member.community_id)].append(user)

        peer_groups: list[dict] = []
        for community in communities[:3]:
            member_profiles = await self._build_profiles(
                tenant_id=tenant_id,
                current_user_id=user_id,
                users=members_by_community.get(int(community.id), [])[:4],
                following_ids=following_ids,
            )
            peer_groups.append(
                {
                    "title": community.name,
                    "description": f"Group learning around {community.topic_id} with shared progress and discussion momentum.",
                    "members": member_profiles,
                }
            )

        return {
            "me": me_profile,
            "following": following_profiles,
            "suggested_people": suggested_profiles,
            "feed": feed,
            "peer_groups": peer_groups,
        }
