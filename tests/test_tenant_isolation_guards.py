import asyncio

import pytest

from app.application.exceptions import NotFoundError
from app.application.services.roadmap_service import RoadmapService


class _DummySession:
    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


class _DummyDiagnosticRepo:
    def __init__(self, scores):
        self._scores = scores

    async def topic_scores_for_test(self, test_id: int, user_id: int, tenant_id: int):
        return self._scores


class _DummyRoadmapRepo:
    async def get_by_identity(self, *, user_id, goal_id, test_id, tenant_id):
        return None

    async def create_roadmap(self, user_id, goal_id, test_id, generated_at, status="generating", error_message=None):
        roadmap = type("RoadmapStub", (), {})()
        roadmap.id = 1
        roadmap.steps = []
        roadmap.status = status
        roadmap.error_message = error_message
        return roadmap

    async def clear_steps(self, roadmap):
        return None

    async def mark_status(self, roadmap, *, status, error_message=None):
        roadmap.status = status
        roadmap.error_message = error_message
        return roadmap


def test_roadmap_generate_raises_when_diagnostic_not_accessible():
    service = RoadmapService(_DummySession())
    service.diagnostic_repository = _DummyDiagnosticRepo(scores={})
    service.roadmap_repository = _DummyRoadmapRepo()

    with pytest.raises(NotFoundError, match="Diagnostic result not found or unauthorized"):
        asyncio.run(service.generate(user_id=1, tenant_id=10, goal_id=100, test_id=999))
