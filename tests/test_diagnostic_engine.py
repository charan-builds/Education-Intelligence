from app.application.services.recommendation_service import RecommendationService, build_recommendation_engine
from app.domain.engines.ml_recommendation_engine import MLRecommendationEngine
from app.domain.engines.rule_engine import RuleEngine


def test_rule_engine_classification():
    service = RecommendationService(RuleEngine())
    result = service.classify_topics({1: 49.0, 2: 60.0, 3: 99.0})
    assert result[1] == "beginner"
    assert result[2] == "needs_practice"
    assert result[3] == "mastered"


def test_prerequisite_expansion_order():
    service = RecommendationService(RuleEngine())
    topic_scores = {10: 40.0, 20: 80.0}
    edges = [(10, 5), (5, 2), (10, 1)]
    sequence = service.weak_topics_with_foundations(topic_scores, edges)
    assert 10 in sequence
    assert 5 in sequence
    assert 2 in sequence
    assert 1 in sequence
    assert 20 not in sequence


def test_ml_engine_accepts_profile_and_returns_steps():
    service = RecommendationService(MLRecommendationEngine())
    topic_scores = {1: 45.0, 2: 67.0, 3: 92.0}
    steps = service.weak_topics_with_foundations(
        topic_scores=topic_scores,
        prerequisite_edges=[],
        learning_profile={"profile_type": "practice_focused"},
        goal={"goal_id": 1},
    )
    assert 1 in steps
    assert 2 in steps
    assert 3 not in steps


def test_engine_factory_defaults_to_rule_for_unknown_values():
    engine = build_recommendation_engine("unknown")
    assert isinstance(engine, RuleEngine)
