from app.domain.engines.content_recommendation_engine import ContentRecommendationEngine


def test_prioritizes_weak_topics_first():
    engine = ContentRecommendationEngine()
    resources = engine.recommend_resources(
        user_learning_profile={"profile_type": "balanced"},
        topic_scores={10: 92.0, 2: 45.0, 7: 68.0},
        goal={"name": "AI/ML Engineer"},
        resources_per_topic=1,
    )
    # Weak topics sorted by score asc => topic 2 then topic 7.
    assert [r.topic_id for r in resources] == [2, 7]


def test_is_deterministic_for_same_inputs():
    engine = ContentRecommendationEngine()
    payload = {
        "user_learning_profile": {"profile_type": "practice_focused"},
        "topic_scores": {1: 40.0, 2: 65.0, 3: 80.0},
        "goal": {"name": "Data Analyst"},
        "resources_per_topic": 2,
    }
    first = engine.recommend_resources(**payload)
    second = engine.recommend_resources(**payload)
    assert first == second


def test_resource_types_are_limited_to_supported_types():
    engine = ContentRecommendationEngine()
    resources = engine.recommend_resources(
        user_learning_profile={"profile_type": "concept_focused"},
        topic_scores={4: 35.0},
        goal={"name": "Web Developer"},
        resources_per_topic=4,
    )
    assert {r.resource_type for r in resources}.issubset({"course", "video", "project", "documentation"})
