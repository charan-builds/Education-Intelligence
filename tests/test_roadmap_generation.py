from app.application.services.recommendation_service import RecommendationService
from app.domain.engines.rule_engine import RuleEngine


def test_roadmap_topic_order_respects_weak_foundations():
    service = RecommendationService(RuleEngine())
    topic_scores = {
        100: 45.0,
        200: 65.0,
        300: 90.0,
    }
    edges = [
        (100, 50),
        (50, 25),
        (200, 60),
    ]
    order = service.weak_topics_with_foundations(topic_scores, edges)
    assert 25 in order
    assert 50 in order
    assert 100 in order
    assert 60 in order
    assert 200 in order
    assert 300 not in order
