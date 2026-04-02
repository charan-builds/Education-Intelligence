import asyncio
from types import SimpleNamespace

import pytest

from app.application.exceptions import ConflictError, NotFoundError
from app.application.services.goal_service import GoalService


class _Session:
    async def commit(self):
        return None

    async def rollback(self):
        return None


class _GoalRepository:
    def __init__(self):
        self.session = _Session()
        self.goal = SimpleNamespace(id=1, name="AI Engineer", description="Build AI systems")
        self.links = []

    async def list_all(self, limit: int, offset: int, cursor_id: int | None = None):
        _ = limit, offset, cursor_id
        return [self.goal]

    async def count_all(self):
        return 1

    async def get_by_id(self, goal_id: int):
        return self.goal if goal_id == 1 else None

    async def get_by_name(self, name: str):
        return self.goal if name == self.goal.name else None

    async def create_goal(self, name: str, description: str):
        return SimpleNamespace(id=2, name=name, description=description)

    async def update_goal(self, goal, **updates):
        for key, value in updates.items():
            setattr(goal, key, value)
        return goal

    async def delete_goal(self, goal):
        _ = goal
        return None

    async def list_topic_links(self, goal_id: int | None = None):
        _ = goal_id
        return list(self.links)

    async def get_topic_link(self, goal_id: int, topic_id: int):
        for link in self.links:
            if link.goal_id == goal_id and link.topic_id == topic_id:
                return link
        return None

    async def get_topic_link_by_id(self, link_id: int):
        for link in self.links:
            if link.id == link_id:
                return link
        return None

    async def create_topic_link(self, goal_id: int, topic_id: int):
        link = SimpleNamespace(id=4, goal_id=goal_id, topic_id=topic_id)
        self.links.append(link)
        return link

    async def delete_topic_link(self, link):
        self.links = [item for item in self.links if item.id != link.id]


class _TopicRepository:
    async def get_topic(self, topic_id: int):
        if topic_id == 7:
            return SimpleNamespace(id=7, name="Linear Algebra")
        return None


def test_create_goal_rejects_duplicate_name():
    async def _run():
        service = GoalService(session=_Session())
        service.repository = _GoalRepository()
        service.topic_repository = _TopicRepository()

        with pytest.raises(ConflictError):
            await service.create_goal(name="AI Engineer", description="Duplicate")

    asyncio.run(_run())


def test_create_goal_topic_requires_existing_topic():
    async def _run():
        service = GoalService(session=_Session())
        service.repository = _GoalRepository()
        service.topic_repository = _TopicRepository()

        with pytest.raises(NotFoundError):
            await service.create_goal_topic(goal_id=1, topic_id=999)

    asyncio.run(_run())


def test_create_goal_topic_returns_link():
    async def _run():
        service = GoalService(session=_Session())
        service.repository = _GoalRepository()
        service.topic_repository = _TopicRepository()

        link = await service.create_goal_topic(goal_id=1, topic_id=7)
        assert link.goal_id == 1
        assert link.topic_id == 7

    asyncio.run(_run())


def test_tenant_scoped_goal_lookup_hides_foreign_goal():
    class _TenantAwareGoalRepository(_GoalRepository):
        async def get_by_id(self, tenant_id: int, goal_id: int):
            if tenant_id == 1 and goal_id == 1:
                return self.goal
            return None

        async def get_by_name(self, tenant_id: int, name: str):
            if tenant_id == 1 and name == self.goal.name:
                return self.goal
            return None

    async def _run():
        service = GoalService(session=_Session())
        service.repository = _TenantAwareGoalRepository()
        service.topic_repository = _TopicRepository()

        with pytest.raises(NotFoundError):
            await service.update_goal(tenant_id=2, goal_id=1, name="Blocked")

        with pytest.raises(NotFoundError):
            await service.delete_goal(tenant_id=2, goal_id=1)

    asyncio.run(_run())
