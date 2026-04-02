from app.application.services.adaptive_engine_service import AdaptiveEngineService


def test_fast_and_accurate_answers_increase_difficulty():
    service = AdaptiveEngineService()

    decision = service.evaluate_answer(
        topic_id=11,
        current_difficulty=2,
        score=100.0,
        time_taken=12.0,
        attempt_count=1,
    )

    assert decision.recommended_difficulty == 3
    assert decision.rule == "increase_difficulty"
    assert decision.level == "advanced"


def test_slow_and_incorrect_answers_reduce_difficulty():
    service = AdaptiveEngineService()

    decision = service.evaluate_answer(
        topic_id=11,
        current_difficulty=2,
        score=0.0,
        time_taken=66.0,
        attempt_count=2,
    )

    assert decision.recommended_difficulty == 1
    assert decision.rule == "reduce_difficulty"
    assert decision.level == "beginner"


def test_classify_topic_levels_groups_rows_per_topic():
    service = AdaptiveEngineService()

    profiles = service.classify_topic_levels(
        [
            {"topic_id": 10, "difficulty": 2, "accuracy": 0.95, "time_taken": 14.0, "attempt_count": 1},
            {"topic_id": 10, "difficulty": 3, "accuracy": 0.9, "time_taken": 19.0, "attempt_count": 1},
            {"topic_id": 20, "difficulty": 2, "accuracy": 0.4, "time_taken": 57.0, "attempt_count": 3},
        ]
    )

    assert profiles[0].topic_id == 10
    assert profiles[0].level == "advanced"
    assert profiles[0].recommended_difficulty == 3
    assert profiles[1].topic_id == 20
    assert profiles[1].level == "beginner"
    assert profiles[1].recommended_difficulty == 1
