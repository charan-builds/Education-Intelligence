from types import SimpleNamespace

import pytest

from app.application.services.diagnostic_service import DiagnosticService


class _FakeDiagnosticRepository:
    async def topic_scores_for_test(self, test_id: int, user_id: int, tenant_id: int) -> dict[int, float]:
        _ = test_id, user_id, tenant_id
        return {10: 42.0, 11: 81.0, 12: 58.0}

    async def get_test_for_user(self, test_id: int, user_id: int, tenant_id: int):
        _ = test_id, user_id, tenant_id
        return SimpleNamespace(goal_id=3)


class _FakeRoadmapRepository:
    async def get_by_identity(self, user_id: int, goal_id: int, test_id: int, tenant_id: int):
        _ = user_id, goal_id, test_id, tenant_id
        return None


class _FakeTopicRepository:
    async def get_prerequisite_edges(self, tenant_id: int) -> list[tuple[int, int]]:
        _ = tenant_id
        return [(10, 5), (12, 10)]


class _FakeRecommendationEngine:
    @staticmethod
    def classify_topic(score: float) -> str:
        if score < 50:
            return "beginner"
        if score <= 70:
            return "needs practice"
        return "mastered"


@pytest.mark.asyncio
async def test_get_result_includes_blueprint_learning_insights() -> None:
    service = DiagnosticService(session=SimpleNamespace())
    service.diagnostic_repository = _FakeDiagnosticRepository()
    service.roadmap_repository = _FakeRoadmapRepository()
    service.topic_repository = _FakeTopicRepository()
    service.recommendation_service = SimpleNamespace(engine=_FakeRecommendationEngine())

    result = await service.get_result(test_id=9, user_id=8, tenant_id=2)

    assert result["test_id"] == 9
    assert result["weak_topic_ids"] == [10, 12]
    assert result["foundation_gap_topic_ids"] == [5, 10]
    assert result["recommendation_levels"] == {10: "beginner", 11: "mastered", 12: "needs practice"}
