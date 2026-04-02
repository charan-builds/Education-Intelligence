from types import SimpleNamespace

from app.application.services.diagnostic_service import DiagnosticService


def test_diagnostic_scoring_accepts_alias_answers():
    service = DiagnosticService(session=SimpleNamespace())
    score = service._score_answer(
        expected_answer="standard deviation",
        user_answer="std deviation",
        accepted_answers=["std deviation", "std. deviation"],
    )
    assert score == 100.0


def test_diagnostic_scoring_rejects_wrong_answers():
    service = DiagnosticService(session=SimpleNamespace())
    score = service._score_answer(
        expected_answer="overfitting",
        user_answer="underfitting",
        accepted_answers=["over-fitting"],
    )
    assert score == 0.0
