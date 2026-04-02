import asyncio
from dataclasses import dataclass

import pytest

from app.application.exceptions import NotFoundError
from app.application.services.resource_service import ResourceService


@dataclass
class _Resource:
    id: int
    tenant_id: int
    topic_id: int
    goal_id: int | None
    difficulty: str
    rating: float
    goal_relevance: float


class _Session:
    async def commit(self):
        return None

    async def rollback(self):
        return None


class _Repo:
    def __init__(self):
        self.add_calls = []

    async def add_resource(self, **kwargs):
        self.add_calls.append(kwargs)
        return _Resource(
            id=1,
            tenant_id=kwargs["tenant_id"],
            topic_id=kwargs["topic_id"],
            goal_id=kwargs.get("goal_id"),
            difficulty=kwargs["difficulty"],
            rating=kwargs["rating"],
            goal_relevance=kwargs["goal_relevance"],
        )

    async def search_resources_by_topic(self, **kwargs):
        return [kwargs]

    async def recommend_resources_for_topics(self, **kwargs):
        topic_ids = kwargs["topic_ids"]
        return [
            _Resource(id=1, tenant_id=kwargs["tenant_id"], topic_id=topic_ids[0], goal_id=kwargs.get("goal_id"), difficulty="easy", rating=4.9, goal_relevance=0.9),
            _Resource(id=2, tenant_id=kwargs["tenant_id"], topic_id=topic_ids[0], goal_id=kwargs.get("goal_id"), difficulty="medium", rating=4.7, goal_relevance=0.8),
            _Resource(id=3, tenant_id=kwargs["tenant_id"], topic_id=topic_ids[1], goal_id=kwargs.get("goal_id"), difficulty="hard", rating=4.6, goal_relevance=0.7),
        ]


class _TopicRepo:
    def __init__(self, valid_topic_ids: set[int] | None = None):
        self.valid_topic_ids = valid_topic_ids or {4, 7, 8, 10, 11}

    async def get_topic(self, topic_id: int, tenant_id: int | None = None):
        _ = tenant_id
        if topic_id in self.valid_topic_ids:
            return {"id": topic_id}
        return None


class _GoalRepo:
    def __init__(self, valid_goal_ids: set[int] | None = None):
        self.valid_goal_ids = valid_goal_ids or {2, 3, 9}

    async def get_by_id(self, tenant_id: int, goal_id: int):
        _ = tenant_id
        if goal_id in self.valid_goal_ids:
            return {"id": goal_id}
        return None


def test_add_resource_commits_and_returns_resource():
    async def _run():
        service = ResourceService(_Session())
        repo = _Repo()
        service.resource_repository = repo
        service.topic_repository = _TopicRepo()
        service.goal_repository = _GoalRepo()

        created = await service.add_resource(
            tenant_id=1,
            topic_id=10,
            goal_id=3,
            resource_type="course",
            title="T10 Course",
            url="https://example.com/t10",
            difficulty="medium",
            rating=4.8,
            goal_relevance=0.9,
        )

        assert created.topic_id == 10
        assert repo.add_calls[0]["tenant_id"] == 1

    asyncio.run(_run())


def test_search_resources_by_topic_forwards_filters():
    async def _run():
        service = ResourceService(_Session())
        repo = _Repo()
        service.resource_repository = repo
        service.topic_repository = _TopicRepo()
        service.goal_repository = _GoalRepo()

        rows = await service.search_resources_by_topic(
            tenant_id=5,
            topic_id=8,
            difficulty="hard",
            min_rating=4.5,
            min_goal_relevance=0.75,
            goal_id=2,
        )

        assert rows[0]["tenant_id"] == 5
        assert rows[0]["difficulty"] == "hard"
        assert rows[0]["goal_id"] == 2

    asyncio.run(_run())


def test_recommend_resources_for_user_prioritizes_weak_topics():
    async def _run():
        service = ResourceService(_Session())
        repo = _Repo()
        service.resource_repository = repo
        service.topic_repository = _TopicRepo()
        service.goal_repository = _GoalRepo()

        resources = await service.recommend_resources_for_user(
            tenant_id=1,
            topic_scores={11: 85.0, 4: 40.0, 7: 65.0},
            goal_id=9,
            min_rating=4.0,
            min_goal_relevance=0.6,
            per_topic_limit=1,
        )

        # weak topics ordered by score => 4 then 7
        assert [r.topic_id for r in resources] == [4, 7]

    asyncio.run(_run())


def test_add_resource_requires_tenant_owned_topic_and_goal():
    async def _run():
        service = ResourceService(_Session())
        service.resource_repository = _Repo()
        service.topic_repository = _TopicRepo(valid_topic_ids={10})
        service.goal_repository = _GoalRepo(valid_goal_ids={3})

        with pytest.raises(NotFoundError):
            await service.add_resource(
                tenant_id=1,
                topic_id=999,
                goal_id=3,
                resource_type="course",
                title="Invalid topic",
                url="https://example.com/invalid",
                difficulty="easy",
                rating=4.0,
                goal_relevance=0.5,
            )

        with pytest.raises(NotFoundError):
            await service.add_resource(
                tenant_id=1,
                topic_id=10,
                goal_id=999,
                resource_type="course",
                title="Invalid goal",
                url="https://example.com/invalid-goal",
                difficulty="easy",
                rating=4.0,
                goal_relevance=0.5,
            )

    asyncio.run(_run())


def test_recommend_resources_requires_tenant_owned_topics_and_goal():
    async def _run():
        service = ResourceService(_Session())
        service.resource_repository = _Repo()
        service.topic_repository = _TopicRepo(valid_topic_ids={4, 7})
        service.goal_repository = _GoalRepo(valid_goal_ids={9})

        with pytest.raises(NotFoundError):
            await service.recommend_resources_for_user(
                tenant_id=1,
                topic_scores={4: 40.0, 99: 70.0},
                goal_id=9,
            )

        with pytest.raises(NotFoundError):
            await service.recommend_resources_for_user(
                tenant_id=1,
                topic_scores={4: 40.0, 7: 70.0},
                goal_id=999,
            )

    asyncio.run(_run())
