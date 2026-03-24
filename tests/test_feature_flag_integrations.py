from app.application.services.mentor_service import MentorAdvice, MentorService
from app.application.services.recommendation_service import RecommendationService
from app.domain.engines.adaptive_testing_engine import AdaptiveQuestion, AdaptiveTestingEngine
from app.domain.engines.ml_recommendation_engine import MLRecommendationEngine


def test_recommendation_service_feature_flag_disables_ml_engine():
    service = RecommendationService(MLRecommendationEngine())
    topic_scores = {1: 40.0, 2: 60.0, 3: 95.0}
    result = service.weak_topics_with_foundations(
        topic_scores=topic_scores,
        prerequisite_edges=[],
        learning_profile={"profile_type": "slow_deep_learner"},
        goal={"goal_id": 1},
        feature_flags={"ml_recommendation_enabled": False},
    )
    # Rule engine fallback excludes mastered topic 3.
    assert 1 in result and 2 in result and 3 not in result


def test_mentor_service_feature_flag_disables_ai_mentor():
    class _FakeLLMAdvisor:
        def generate_advice(self, diagnostic_results, roadmap_progress, learning_profile):
            return MentorAdvice(summary="LLM", recommendations=["A"], risk_level="low")

    service = MentorService(advisor=_FakeLLMAdvisor())
    result = service.get_personalized_advice(
        diagnostic_results={1: 10.0},
        roadmap_progress={"completion_rate": 10.0, "overdue_steps": 2},
        learning_profile={"profile_type": "practice_focused"},
        feature_flags={"ai_mentor_enabled": False},
    )
    assert result["advisor_type"] == "RuleBasedMentorAdvisor"


def test_adaptive_engine_feature_flag_disables_adaptive_behavior():
    engine = AdaptiveTestingEngine()
    questions = [
        AdaptiveQuestion(id=1, topic_id=10, difficulty=1, question_type="multiple_choice", question_text="q1"),
        AdaptiveQuestion(id=2, topic_id=10, difficulty=2, question_type="multiple_choice", question_text="q2"),
        AdaptiveQuestion(id=3, topic_id=10, difficulty=3, question_type="multiple_choice", question_text="q3"),
    ]
    previous = [{"question_id": 2, "score": 95.0}, {"question_id": 3, "score": 95.0}]
    next_q = engine.select_next_question(
        questions=questions,
        previous_answers=previous,
        topic_scores={10: 20.0},
        feature_flags={"adaptive_testing_enabled": False},
    )
    assert next_q is not None
    assert next_q.id == 1
