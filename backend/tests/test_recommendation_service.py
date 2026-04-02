import asyncio

from app.application.services.recommendation_service import RecommendationService
from app.domain.engines.ml_recommendation_engine import MLRecommendationEngine


def test_rank_topics_exposes_explainable_priority_components():
    service = RecommendationService(MLRecommendationEngine())

    ranked = service.rank_topics(
        topic_scores={1: 42.0, 2: 68.0, 3: 90.0},
        prerequisite_edges=[(2, 1), (3, 2)],
        learning_profile={
            "profile_type": "practice_focused",
            "confidence_by_topic": {1: 0.4, 2: 0.7, 3: 0.9},
            "days_since_last_interaction_by_topic": {1: 16, 2: 5, 3: 2},
            "velocity_by_topic": {1: 0.3, 2: 0.6, 3: 0.9},
            "difficulty_by_topic": {1: 0.7, 2: 0.5, 3: 0.2},
        },
        goal={"importance_by_topic": {1: 0.9, 2: 0.8, 3: 0.4}},
    )

    assert ranked[0].topic_id == 1
    assert ranked[0].components is not None
    assert ranked[0].components.priority_score > ranked[-1].priority_score
    assert "prioritized because of" in ranked[0].explanation


def test_async_recommendation_falls_back_to_engine_when_ai_is_processing(monkeypatch):
    class _FakeAIRequestService:
        def __init__(self, session):
            self.session = session

        async def queue_learning_path_recommendation(self, **kwargs):
            return {"request_id": "learning-path-1", "status": "processing"}

    monkeypatch.setattr(
        "app.application.services.recommendation_service.AIRequestService",
        _FakeAIRequestService,
    )

    service = RecommendationService(MLRecommendationEngine(), session=object())

    async def _run():
        result = await service.weak_topics_with_foundations_async(
            topic_scores={1: 45.0, 2: 67.0, 3: 92.0},
            prerequisite_edges=[],
            user_id=7,
            tenant_id=3,
            learning_profile={"profile_type": "practice_focused"},
            goal={"goal_id": 1},
            feature_flags={"ml_recommendation_enabled": True},
        )
        assert 1 in result
        assert 2 in result
        assert 3 not in result

    asyncio.run(_run())
