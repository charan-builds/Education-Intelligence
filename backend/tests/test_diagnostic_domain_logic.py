from types import SimpleNamespace

from app.application.services.diagnostic.scoring_service import DiagnosticScoringService


scoring_service = DiagnosticScoringService()


def test_accuracy_from_score_bounds_to_unit_interval():
    assert scoring_service.accuracy_from_score(-10) == 0.0
    assert scoring_service.accuracy_from_score(50) == 0.5
    assert scoring_service.accuracy_from_score(120) == 1.0


def test_build_adaptive_rows_uses_question_and_answer_data():
    answers = [
        SimpleNamespace(question_id=11, score=80.0, time_taken=7.5, attempt_count=2),
        SimpleNamespace(question_id=12, score=40.0, time_taken=5.0),
    ]
    questions_by_id = {
        11: SimpleNamespace(topic_id=101, difficulty=3),
        12: SimpleNamespace(topic_id=102, difficulty=1),
    }

    rows = scoring_service.build_adaptive_rows(answers=answers, questions_by_id=questions_by_id)

    assert rows == [
        {
            "topic_id": 101,
            "difficulty": 3,
            "accuracy": 0.8,
            "time_taken": 7.5,
            "attempt_count": 2,
        },
        {
            "topic_id": 102,
            "difficulty": 1,
            "accuracy": 0.4,
            "time_taken": 5.0,
            "attempt_count": 1,
        },
    ]


def test_weighted_score_uses_difficulty_weights():
    results = [
        {"question_id": 1, "is_correct": False, "difficulty_label": "easy"},
        {"question_id": 2, "is_correct": True, "difficulty_label": "medium"},
        {"question_id": 3, "is_correct": True, "difficulty_label": "hard"},
    ]

    assert scoring_service.weighted_score(results) == 83.33
    assert scoring_service.percentage_score(results) == 83.33


def test_score_question_answer_includes_weight_from_question_difficulty():
    question = SimpleNamespace(
        id=7,
        topic_id=101,
        correct_answer="binary search",
        accepted_answers=[],
        difficulty_level=3,
        difficulty_label="hard",
    )

    result = scoring_service.score_question_answer(
        question=question,
        question_id=7,
        user_answer="binary search",
    )

    assert result["is_correct"] is True
    assert result["difficulty_weight"] == 3
