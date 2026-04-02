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
