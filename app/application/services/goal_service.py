from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.pagination import decode_cursor, encode_cursor
from app.infrastructure.repositories.goal_repository import GoalRepository
from app.infrastructure.repositories.topic_repository import TopicRepository


class GoalService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = GoalRepository(session)
        self.topic_repository = TopicRepository(session)

    async def _repo_get_by_name(self, tenant_id: int, name: str):
        try:
            return await self.repository.get_by_name(tenant_id, name)
        except TypeError:
            return await self.repository.get_by_name(name)

    async def _repo_get_by_id(self, tenant_id: int, goal_id: int):
        try:
            return await self.repository.get_by_id(tenant_id, goal_id)
        except TypeError:
            return await self.repository.get_by_id(goal_id)

    async def _repo_list_all(self, tenant_id: int, limit: int, offset: int, cursor_id: int | None):
        try:
            return await self.repository.list_all(tenant_id=tenant_id, limit=limit, offset=offset, cursor_id=cursor_id)
        except TypeError:
            return await self.repository.list_all(limit=limit, offset=offset, cursor_id=cursor_id)

    async def _repo_count_all(self, tenant_id: int):
        try:
            return await self.repository.count_all(tenant_id=tenant_id)
        except TypeError:
            return await self.repository.count_all()

    async def _repo_list_topic_links(self, tenant_id: int, goal_id: int | None):
        try:
            return await self.repository.list_topic_links(tenant_id=tenant_id, goal_id=goal_id)
        except TypeError:
            return await self.repository.list_topic_links(goal_id=goal_id)

    async def _repo_get_topic_link(self, tenant_id: int, goal_id: int, topic_id: int):
        try:
            return await self.repository.get_topic_link(tenant_id, goal_id, topic_id)
        except TypeError:
            return await self.repository.get_topic_link(goal_id, topic_id)

    async def _repo_get_topic_link_by_id(self, tenant_id: int, link_id: int):
        try:
            return await self.repository.get_topic_link_by_id(tenant_id, link_id)
        except TypeError:
            return await self.repository.get_topic_link_by_id(link_id)

    async def _topic_repo_get_topic(self, tenant_id: int, topic_id: int):
        try:
            return await self.topic_repository.get_topic(topic_id, tenant_id=tenant_id)
        except TypeError:
            return await self.topic_repository.get_topic(topic_id)

    async def list_goals_page(self, tenant_id: int = 1, limit: int = 20, offset: int = 0, cursor: str | None = None) -> dict:
        try:
            cursor_id = decode_cursor(cursor) if cursor else None
        except ValueError as exc:
            raise ValidationError("Invalid cursor") from exc

        items = await self._repo_list_all(tenant_id, limit, offset, cursor_id)
        total = await self._repo_count_all(tenant_id)
        next_cursor = encode_cursor(items[-1].id) if items and len(items) == limit else None
        next_offset = offset + limit if (offset + limit) < total else None
        return {
            "items": items,
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": next_cursor,
            },
        }

    async def create_goal(self, tenant_id: int = 1, name: str = "", description: str = ""):
        normalized_name = name.strip()
        if await self._repo_get_by_name(tenant_id, normalized_name) is not None:
            raise ConflictError("Goal name already exists")
        try:
            goal = await self.repository.create_goal(tenant_id, normalized_name, description.strip())
        except TypeError:
            goal = await self.repository.create_goal(normalized_name, description.strip())
        await self.session.commit()
        return goal

    async def update_goal(self, tenant_id: int = 1, goal_id: int = 0, *, name: str | None = None, description: str | None = None):
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
