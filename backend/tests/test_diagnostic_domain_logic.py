from types import SimpleNamespace

from app.domain.models.diagnostic_test import DiagnosticTest


def test_accuracy_from_score_bounds_to_unit_interval():
    assert DiagnosticTest.accuracy_from_score(-10) == 0.0
    assert DiagnosticTest.accuracy_from_score(50) == 0.5
    assert DiagnosticTest.accuracy_from_score(120) == 1.0


def test_build_adaptive_rows_uses_question_and_answer_data():
    answers = [
        SimpleNamespace(question_id=11, score=80.0, time_taken=7.5, attempt_count=2),
        SimpleNamespace(question_id=12, score=40.0, time_taken=5.0),
    ]
    questions_by_id = {
        11: SimpleNamespace(topic_id=101, difficulty=3),
        12: SimpleNamespace(topic_id=102, difficulty=1),
    }

    rows = DiagnosticTest.build_adaptive_rows(answers=answers, questions_by_id=questions_by_id)

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
