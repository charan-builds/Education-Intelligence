import asyncio
from types import SimpleNamespace

from fastapi import Response

from app.application.exceptions import NotFoundError
from app.presentation import goal_routes
from app.schemas.common_schema import PaginationParams
from app.schemas.goal_schema import GoalCreateRequest, GoalTopicCreateRequest, GoalUpdateRequest


class _DummySession:
    pass


class _FakeGoalService:
    last_create_goal = None
    last_update_goal = None
    last_delete_goal_id = None
    last_create_goal_topic = None
    last_delete_goal_topic_id = None

    def __init__(self, session):
        self.session = session

    async def list_goals_page(self, limit: int, offset: int, cursor: str | None = None):
        _ = cursor
        return {
            "items": [{"id": 1, "name": "AI Engineer", "description": "Build AI systems"}],
            "meta": {"total": 1, "limit": limit, "offset": offset, "next_offset": None, "next_cursor": None},
        }

    async def create_goal(self, *, name: str, description: str):
        _FakeGoalService.last_create_goal = {"name": name, "description": description}
        return SimpleNamespace(id=2, name=name, description=description)

    async def update_goal(self, goal_id: int, *, name: str | None = None, description: str | None = None):
        _FakeGoalService.last_update_goal = {"goal_id": goal_id, "name": name, "description": description}
        return SimpleNamespace(id=goal_id, name=name or "Existing", description=description or "Updated")

    async def delete_goal(self, goal_id: int):
        _FakeGoalService.last_delete_goal_id = goal_id

    async def list_goal_topics_page(self, goal_id: int | None = None):
        return {
            "items": [{"id": 4, "goal_id": goal_id or 1, "topic_id": 7}],
            "meta": {"total": 1, "limit": 1, "offset": 0, "next_offset": None, "next_cursor": None},
        }

    async def create_goal_topic(self, goal_id: int, topic_id: int):
        _FakeGoalService.last_create_goal_topic = {"goal_id": goal_id, "topic_id": topic_id}
        return SimpleNamespace(id=4, goal_id=goal_id, topic_id=topic_id)

    async def delete_goal_topic(self, link_id: int):
        _FakeGoalService.last_delete_goal_topic_id = link_id


def _user(role: str):
    return SimpleNamespace(role=SimpleNamespace(value=role), tenant_id=1)


def test_create_goal_route(monkeypatch):
    monkeypatch.setattr(goal_routes, "GoalService", _FakeGoalService)

    async def _run():
        result = await goal_routes.create_goal(
            payload=GoalCreateRequest(name="Data Analyst", description="Analyze data"),
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert result.id == 2
        assert _FakeGoalService.last_create_goal == {"name": "Data Analyst", "description": "Analyze data"}

    asyncio.run(_run())


def test_goal_topic_routes(monkeypatch):
    monkeypatch.setattr(goal_routes, "GoalService", _FakeGoalService)

    async def _run():
        listed = await goal_routes.list_goal_topics(
            goal_id=1,
            db=_DummySession(),
            _current_user=_user("teacher"),
        )
        assert listed["items"][0]["topic_id"] == 7

        created = await goal_routes.create_goal_topic(
            payload=GoalTopicCreateRequest(goal_id=1, topic_id=7),
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert created.id == 4

        deleted = await goal_routes.delete_goal_topic(
            link_id=4,
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert isinstance(deleted, Response)
        assert deleted.status_code == 204

    asyncio.run(_run())


def test_update_and_delete_goal_routes(monkeypatch):
    monkeypatch.setattr(goal_routes, "GoalService", _FakeGoalService)

    async def _run():
        updated = await goal_routes.update_goal(
            goal_id=1,
            payload=GoalUpdateRequest(name="ML Engineer"),
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert updated.id == 1
        deleted = await goal_routes.delete_goal(
            goal_id=1,
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert isinstance(deleted, Response)
        assert _FakeGoalService.last_delete_goal_id == 1

    asyncio.run(_run())


def test_goal_route_propagates_not_found_for_foreign_tenant(monkeypatch):
    class _ForeignTenantGoalService(_FakeGoalService):
        async def update_goal(self, goal_id: int, *, name: str | None = None, description: str | None = None):
            _ = goal_id, name, description
            raise NotFoundError("Goal not found")

        async def delete_goal(self, goal_id: int):
            _ = goal_id
            raise NotFoundError("Goal not found")

    monkeypatch.setattr(goal_routes, "GoalService", _ForeignTenantGoalService)

    async def _run():
        try:
            await goal_routes.update_goal(
                goal_id=99,
                payload=GoalUpdateRequest(name="Blocked"),
                db=_DummySession(),
                _current_user=_user("admin"),
            )
            assert False, "Expected NotFoundError"
        except NotFoundError as exc:
            assert "Goal not found" in str(exc)

        try:
            await goal_routes.delete_goal(
                goal_id=99,
                db=_DummySession(),
                _current_user=_user("admin"),
            )
            assert False, "Expected NotFoundError"
        except NotFoundError as exc:
            assert "Goal not found" in str(exc)

    asyncio.run(_run())
