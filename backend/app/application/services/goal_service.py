from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.pagination import decode_cursor, encode_cursor
from app.infrastructure.repositories.goal_repository import GoalRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.infrastructure.repositories.user_goal_repository import UserGoalRepository
from app.infrastructure.repositories.user_profile_repository import UserProfileRepository


class GoalService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = GoalRepository(session)
        self.topic_repository = TopicRepository(session)
        self.user_goal_repository = UserGoalRepository(session)
        self.user_profile_repository = UserProfileRepository(session)

    async def _repo_get_by_name(self, tenant_id: int, name: str):
        return await self.repository.get_by_name(tenant_id, name)

    async def _repo_get_by_id(self, tenant_id: int, goal_id: int):
        return await self.repository.get_by_id(tenant_id, goal_id)

    async def _repo_list_all(self, tenant_id: int, limit: int, offset: int, cursor_id: int | None):
        return await self.repository.list_all(tenant_id=tenant_id, limit=limit, offset=offset, cursor_id=cursor_id)

    async def _repo_count_all(self, tenant_id: int):
        return await self.repository.count_all(tenant_id=tenant_id)

    async def _repo_list_topic_links(self, tenant_id: int, goal_id: int | None):
        return await self.repository.list_topic_links(tenant_id=tenant_id, goal_id=goal_id)

    async def _repo_get_topic_link(self, tenant_id: int, goal_id: int, topic_id: int):
        return await self.repository.get_topic_link(tenant_id, goal_id, topic_id)

    async def _repo_get_topic_link_by_id(self, tenant_id: int, link_id: int):
        return await self.repository.get_topic_link_by_id(tenant_id, link_id)

    async def _topic_repo_get_topic(self, tenant_id: int, topic_id: int):
        return await self.topic_repository.get_topic(topic_id, tenant_id=tenant_id)

    async def list_goals_page(
        self,
        tenant_id: int = 1,
        limit: int = 20,
        offset: int = 0,
        cursor: str | None = None,
        user_id: int | None = None,
    ) -> dict:
        try:
            cursor_id = decode_cursor(cursor) if cursor else None
        except ValueError as exc:
            raise ValidationError("Invalid cursor") from exc

        items = await self._repo_list_all(tenant_id, limit, offset, cursor_id)
        total = await self._repo_count_all(tenant_id)
        recommended_goal_id = None
        if user_id is not None:
            recommended_goal_id = await self._recommend_goal_id(user_id=user_id, tenant_id=tenant_id, goals=items)
        serialized_items = [
            {
                "id": goal.id,
                "tenant_id": goal.tenant_id,
                "name": goal.name,
                "description": goal.description,
                "skills_covered": goal.skills_covered,
                "estimated_duration_weeks": goal.estimated_duration_weeks,
                "difficulty_tag": goal.difficulty_tag,
                "roadmap_preview": goal.roadmap_preview,
                "is_recommended": goal.id == recommended_goal_id,
            }
            for goal in items
        ]
        next_cursor = encode_cursor(items[-1].id) if items and len(items) == limit else None
        next_offset = offset + limit if (offset + limit) < total else None
        return {
            "items": serialized_items,
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": next_cursor,
            },
        }

    async def create_goal(
        self,
        tenant_id: int = 1,
        name: str = "",
        description: str = "",
        *,
        skills_covered: list[str] | None = None,
        estimated_duration_weeks: int | None = None,
        difficulty_tag: str | None = None,
        roadmap_preview: str | None = None,
    ):
        normalized_name = name.strip()
        if await self._repo_get_by_name(tenant_id, normalized_name) is not None:
            raise ConflictError("Goal name already exists")
        goal = await self.repository.create_goal(
            tenant_id,
            normalized_name,
            description.strip(),
            skills_covered=skills_covered,
            estimated_duration_weeks=estimated_duration_weeks,
            difficulty_tag=difficulty_tag,
            roadmap_preview=roadmap_preview,
        )
        await self.session.commit()
        return goal

    async def update_goal(
        self,
        tenant_id: int = 1,
        goal_id: int = 0,
        *,
        name: str | None = None,
        description: str | None = None,
        skills_covered: list[str] | None = None,
        estimated_duration_weeks: int | None = None,
        difficulty_tag: str | None = None,
        roadmap_preview: str | None = None,
    ):
        goal = await self._repo_get_by_id(tenant_id, goal_id)
        if goal is None:
            raise NotFoundError("Goal not found")

        updates: dict[str, str] = {}
        if name is not None:
            normalized_name = name.strip()
            existing = await self._repo_get_by_name(tenant_id, normalized_name)
            if existing is not None and existing.id != goal_id:
                raise ConflictError("Goal name already exists")
            updates["name"] = normalized_name
        if description is not None:
            updates["description"] = description.strip()
        if skills_covered is not None:
            updates["skills_covered"] = skills_covered
        if estimated_duration_weeks is not None:
            updates["estimated_duration_weeks"] = estimated_duration_weeks
        if difficulty_tag is not None:
            updates["difficulty_tag"] = difficulty_tag.strip()
        if roadmap_preview is not None:
            updates["roadmap_preview"] = roadmap_preview.strip()

        updated = await self.repository.update_goal(goal, **updates)
        await self.session.commit()
        return updated

    async def delete_goal(self, tenant_id: int = 1, goal_id: int = 0) -> None:
        goal = await self._repo_get_by_id(tenant_id, goal_id)
        if goal is None:
            raise NotFoundError("Goal not found")
        await self.repository.delete_goal(goal)
        await self.session.commit()

    async def list_goal_topics_page(self, tenant_id: int = 1, goal_id: int | None = None) -> dict:
        items = await self._repo_list_topic_links(tenant_id, goal_id)
        return {
            "items": items,
            "meta": {
                "total": len(items),
                "limit": len(items) if items else 0,
                "offset": 0,
                "next_offset": None,
                "next_cursor": None,
            },
        }

    async def create_goal_topic(self, tenant_id: int = 1, goal_id: int = 0, topic_id: int = 0):
        if await self._repo_get_by_id(tenant_id, goal_id) is None:
            raise NotFoundError("Goal not found")
        if await self._topic_repo_get_topic(tenant_id, topic_id) is None:
            raise NotFoundError("Topic not found")
        if await self._repo_get_topic_link(tenant_id, goal_id, topic_id) is not None:
            raise ConflictError("Goal-topic link already exists")
        link = await self.repository.create_topic_link(goal_id, topic_id)
        await self.session.commit()
        return link

    async def delete_goal_topic(self, tenant_id: int = 1, link_id: int = 0) -> None:
        link = await self._repo_get_topic_link_by_id(tenant_id, link_id)
        if link is None:
            raise NotFoundError("Goal-topic link not found")
        await self.repository.delete_topic_link(link)
        await self.session.commit()

    async def select_goal_for_user(self, *, user_id: int, tenant_id: int, goal_id: int) -> dict:
        goal = await self._repo_get_by_id(tenant_id, goal_id)
        if goal is None:
            raise NotFoundError("Goal not found")
        await self.user_goal_repository.deactivate_all_for_user(user_id=user_id)
        link = await self.user_goal_repository.create_or_activate(user_id=user_id, goal_id=goal_id)
        await self.session.commit()
        await self.session.refresh(link)
        active = await self.user_goal_repository.get_active_for_user(user_id=user_id, tenant_id=tenant_id)
        if active is None or active.goal is None:
            raise NotFoundError("Selected goal could not be loaded")
        return {
            "user_id": active.user_id,
            "goal_id": active.goal_id,
            "is_active": active.is_active,
            "goal": {
                "id": active.goal.id,
                "tenant_id": active.goal.tenant_id,
                "name": active.goal.name,
                "description": active.goal.description,
                "skills_covered": active.goal.skills_covered,
                "estimated_duration_weeks": active.goal.estimated_duration_weeks,
                "difficulty_tag": active.goal.difficulty_tag,
                "roadmap_preview": active.goal.roadmap_preview,
                "is_recommended": False,
            },
        }

    async def get_current_goal_for_user(self, *, user_id: int, tenant_id: int) -> dict | None:
        active = await self.user_goal_repository.get_active_for_user(user_id=user_id, tenant_id=tenant_id)
        if active is None or active.goal is None:
            return None
        return {
            "user_id": active.user_id,
            "goal_id": active.goal_id,
            "is_active": active.is_active,
            "goal": {
                "id": active.goal.id,
                "tenant_id": active.goal.tenant_id,
                "name": active.goal.name,
                "description": active.goal.description,
                "skills_covered": active.goal.skills_covered,
                "estimated_duration_weeks": active.goal.estimated_duration_weeks,
                "difficulty_tag": active.goal.difficulty_tag,
                "roadmap_preview": active.goal.roadmap_preview,
                "is_recommended": False,
            },
        }

    async def _recommend_goal_id(self, *, user_id: int, tenant_id: int, goals: list) -> int | None:
        if not goals:
            return None
        profile = await self.user_profile_repository.get_for_user(user_id=user_id, tenant_id=tenant_id)
        experience_level = str(getattr(profile, "experience_level", "") or "").strip().lower()
        preferred_tags = {
            "beginner": ("beginner", "easy"),
            "intermediate": ("intermediate", "medium"),
            "advanced": ("advanced", "hard"),
        }.get(experience_level, ("beginner", "easy"))
        for tag in preferred_tags:
            match = next((goal for goal in goals if str(getattr(goal, "difficulty_tag", "") or "").strip().lower() == tag), None)
            if match is not None:
                return match.id
        return goals[0].id
