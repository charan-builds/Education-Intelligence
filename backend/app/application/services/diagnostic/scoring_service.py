from __future__ import annotations

from types import SimpleNamespace

from app.domain.services import diagnostic_rules


class DiagnosticScoringService:
    """Pure diagnostic answer scoring helpers.

    The service is intentionally stateless so unit tests can exercise scoring
    without a database session or ORM models.
    """

    def evaluate_answers(self, answers: list[dict], questions_by_id: dict[int, object]) -> list[dict]:
        return diagnostic_rules.evaluate_answers(answers, questions_by_id)

    def calculate_score(
        self,
        *,
        expected_answer: str,
        user_answer: str,
        accepted_answers: list[str] | None = None,
    ) -> float:
        question = SimpleNamespace(
            correct_answer=expected_answer,
            accepted_answers=list(accepted_answers or []),
        )
        evaluated = self.evaluate_answers(
            [{"question_id": 0, "user_answer": user_answer}],
            {0: question},
        )
        return float(evaluated[0]["score"]) if evaluated else 0.0

    def score_question_answer(
        self,
        *,
        question: object,
        question_id: int,
        user_answer: str,
        attempt_count: int = 1,
    ) -> dict:
        evaluated = self.evaluate_answers(
            [
                {
                    "question_id": int(question_id),
                    "user_answer": user_answer,
                    "attempt_count": int(attempt_count),
                }
            ],
            {int(getattr(question, "id")): question},
        )
        if not evaluated:
            difficulty_weight = self.difficulty_weight(question)
            return {
                "question_id": int(question_id),
                "user_answer": user_answer,
                "attempt_count": int(attempt_count),
                "score": 0.0,
                "accuracy": 0.0,
                "is_correct": False,
                "difficulty_weight": difficulty_weight,
                "difficulty_level": difficulty_weight,
            }
        result = evaluated[0]
        score = float(result["score"])
        difficulty_weight = self.difficulty_weight(question)
        return {
            **result,
            "score": score,
            "accuracy": float(result["accuracy"]),
            "is_correct": score >= 100.0,
            "difficulty_weight": difficulty_weight,
            "difficulty_level": difficulty_weight,
        }

    def accuracy_from_score(self, score: float) -> float:
        return diagnostic_rules.accuracy_from_score(score)

    def build_adaptive_rows(self, *, answers: list[object], questions_by_id: dict[int, object]) -> list[dict]:
        return diagnostic_rules.build_adaptive_rows(answers=answers, questions_by_id=questions_by_id)

    @staticmethod
    def difficulty_weight(question_or_result: object) -> int:
        return diagnostic_rules.difficulty_weight(question_or_result)

    @staticmethod
    def weighted_score(results: list[dict]) -> float:
        return diagnostic_rules.weighted_score(results)

    @staticmethod
    def total_score(results: list[dict]) -> float:
        return round(sum(float(item["score"]) for item in results), 2)

    @staticmethod
    def percentage_score(results: list[dict]) -> float:
        return diagnostic_rules.weighted_score(results)
