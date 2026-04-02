import asyncio
import sys
from types import SimpleNamespace
from types import ModuleType

import pytest
from fastapi import HTTPException

from app.application.exceptions import NotFoundError
from app.schemas.roadmap_schema import RoadmapStepUpdateRequest


fake_celery = ModuleType("celery")


class _FakeCelery:
    def __init__(self, *args, **kwargs):
        _ = args, kwargs
        self.conf = SimpleNamespace(update=lambda **kw: None)

    def config_from_object(self, *args, **kwargs):
        _ = args, kwargs

    def send_task(self, *args, **kwargs):
        _ = args, kwargs
        return None

    def autodiscover_tasks(self, *args, **kwargs):
        _ = args, kwargs

    def task(self, *args, **kwargs):
        _ = args, kwargs

        def _decorator(func):
            return func

        return _decorator


fake_celery.Celery = _FakeCelery
sys.modules.setdefault("celery", fake_celery)

from app.presentation import roadmap_routes


class _DummySession:
    pass


async def _noop(*args, **kwargs):
    _ = args, kwargs
    return None


class _FakeRoadmapService:
    should_raise_not_found = False
    should_enqueue = False
    last_update = None
    last_generation = None
    generated_now = None

    def __init__(self, session):
        self.session = session

    async def ensure_generation_requested(self, **kwargs):
        _FakeRoadmapService.last_generation = kwargs
        roadmap = SimpleNamespace(
            id=44,
            user_id=kwargs["user_id"],
            goal_id=kwargs["goal_id"],
            test_id=kwargs["test_id"],
            status="ready",
            error_message=None,
            generated_at="2026-03-14T00:00:00Z",
            steps=[{"id": 99}],
        )
        return roadmap, self.should_enqueue

    async def generate(self, **kwargs):
        _FakeRoadmapService.generated_now = kwargs
        return SimpleNamespace(
            id=45,
            user_id=kwargs["user_id"],
            goal_id=kwargs["goal_id"],
            test_id=kwargs["test_id"],
            status="ready",
            error_message=None,
            generated_at="2026-03-15T00:00:00Z",
            steps=[{"id": 1}],
        )

    def serialize_roadmap(self, roadmap):
        return {
            "id": roadmap.id,
            "user_id": roadmap.user_id,
            "goal_id": roadmap.goal_id,
            "test_id": roadmap.test_id,
            "status": roadmap.status,
            "error_message": roadmap.error_message,
            "generated_at": roadmap.generated_at,
            "steps": list(roadmap.steps),
        }

    async def update_step_status(self, **kwargs):
        _FakeRoadmapService.last_update = kwargs
        if self.should_raise_not_found:
            raise NotFoundError("Roadmap step not found")
        return {
            "id": kwargs["step_id"],
            "topic_id": 101,
            "phase": "Phase 1 - Foundations",
            "estimated_time_hours": 4.0,
            "difficulty": "medium",
            "priority": 1,
            "deadline": "2026-03-14T00:00:00Z",
            "progress_status": kwargs["progress_status"],
        }


def _user(role: str):
    return SimpleNamespace(id=7, tenant_id=3, role=SimpleNamespace(value=role))


def test_patch_roadmap_step_success(monkeypatch):
    monkeypatch.setattr(roadmap_routes, "RoadmapService", _FakeRoadmapService)
    monkeypatch.setattr(roadmap_routes.realtime_hub, "send_user", _noop)
    monkeypatch.setattr(roadmap_routes.realtime_hub, "send_tenant", _noop)

    async def _run():
        result = await roadmap_routes.update_roadmap_step(
            step_id=12,
            payload=RoadmapStepUpdateRequest(progress_status="completed"),
            db=_DummySession(),
            current_user=_user("student"),
        )
        assert result["progress_status"] == "completed"
        assert _FakeRoadmapService.last_update == {
            "step_id": 12,
            "user_id": 7,
            "tenant_id": 3,
            "progress_status": "completed",
        }

    asyncio.run(_run())


def test_patch_roadmap_step_forbidden_for_teacher(monkeypatch):
    monkeypatch.setattr(roadmap_routes, "RoadmapService", _FakeRoadmapService)
    monkeypatch.setattr(roadmap_routes.realtime_hub, "send_user", _noop)
    monkeypatch.setattr(roadmap_routes.realtime_hub, "send_tenant", _noop)

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await roadmap_routes.update_roadmap_step(
                step_id=12,
                payload=RoadmapStepUpdateRequest(progress_status="completed"),
                db=_DummySession(),
                current_user=_user("teacher"),
            )
        assert exc.value.status_code == 403
        assert exc.value.detail == "Only students can update roadmap progress"

    asyncio.run(_run())


def test_patch_roadmap_step_not_found(monkeypatch):
    _FakeRoadmapService.should_raise_not_found = True
    monkeypatch.setattr(roadmap_routes, "RoadmapService", _FakeRoadmapService)
    monkeypatch.setattr(roadmap_routes.realtime_hub, "send_user", _noop)
    monkeypatch.setattr(roadmap_routes.realtime_hub, "send_tenant", _noop)

    async def _run():
        with pytest.raises(NotFoundError):
            await roadmap_routes.update_roadmap_step(
                step_id=999,
                payload=RoadmapStepUpdateRequest(progress_status="completed"),
                db=_DummySession(),
                current_user=_user("student"),
            )

    asyncio.run(_run())
    _FakeRoadmapService.should_raise_not_found = False


def test_generate_roadmap_returns_serialized_response(monkeypatch):
    monkeypatch.setattr(roadmap_routes, "RoadmapService", _FakeRoadmapService)
    monkeypatch.setattr(roadmap_routes.realtime_hub, "send_user", _noop)
    monkeypatch.setattr(roadmap_routes.realtime_hub, "send_tenant", _noop)

    async def _run():
        result = await roadmap_routes.generate_roadmap(
            request=SimpleNamespace(),
            payload=SimpleNamespace(goal_id=9, test_id=55),
            db=SimpleNamespace(),
            current_user=_user("student"),
        )
        assert result["id"] == 44
        assert result["status"] == "ready"
        assert _FakeRoadmapService.last_generation == {
            "user_id": 7,
            "tenant_id": 3,
            "goal_id": 9,
            "test_id": 55,
        }

    asyncio.run(_run())


def test_generate_roadmap_runs_synchronously_when_requested(monkeypatch):
    monkeypatch.setattr(roadmap_routes, "RoadmapService", _FakeRoadmapService)
    monkeypatch.setattr(roadmap_routes.realtime_hub, "send_user", _noop)
    monkeypatch.setattr(roadmap_routes.realtime_hub, "send_tenant", _noop)
    _FakeRoadmapService.should_enqueue = True
    _FakeRoadmapService.generated_now = None

    async def _run():
        result = await roadmap_routes.generate_roadmap(
            request=SimpleNamespace(),
            payload=SimpleNamespace(goal_id=10, test_id=77),
            db=SimpleNamespace(),
            current_user=_user("student"),
        )
        assert result["id"] == 45
        assert result["status"] == "ready"
        assert _FakeRoadmapService.generated_now == {
            "user_id": 7,
            "tenant_id": 3,
            "goal_id": 10,
            "test_id": 77,
        }

    asyncio.run(_run())
    _FakeRoadmapService.should_enqueue = False
