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


def test_roadmap_generate_raises_when_diagnostic_not_accessible():
    service = RoadmapService(_DummySession())
    service.diagnostic_repository = _DummyDiagnosticRepo(scores={})

    with pytest.raises(NotFoundError, match="Diagnostic result not found or unauthorized"):
        asyncio.run(service.generate(user_id=1, tenant_id=10, goal_id=100, test_id=999))
