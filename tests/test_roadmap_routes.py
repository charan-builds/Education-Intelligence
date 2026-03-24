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


fake_celery.Celery = _FakeCelery
sys.modules.setdefault("celery", fake_celery)

from app.presentation import roadmap_routes


class _DummySession:
    pass


class _FakeRoadmapService:
    should_raise_not_found = False
    last_update = None

    def __init__(self, session):
        self.session = session

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
