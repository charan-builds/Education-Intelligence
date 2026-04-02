from __future__ import annotations


def normalize_answer(value: str) -> str:
    return "".join(ch.lower() for ch in value.strip() if ch.isalnum() or ch.isspace()).strip()


def evaluate_answers(answers: list[dict], questions_by_id: dict[int, object]) -> list[dict]:
    evaluated: list[dict] = []
    for answer in answers:
        question = questions_by_id.get(int(answer["question_id"]))
        if question is None:
            continue
        normalized_expected = normalize_answer(str(getattr(question, "correct_answer", "") or ""))
        normalized_user = normalize_answer(str(answer.get("user_answer", "") or ""))
        valid_answers = {normalized_expected} if normalized_expected else set()
        for alias in list(getattr(question, "accepted_answers", []) or []):
            normalized_alias = normalize_answer(str(alias))
            if normalized_alias:
                valid_answers.add(normalized_alias)
        score = 100.0 if normalized_user and normalized_user in valid_answers else 0.0
        evaluated.append(
            {
                **answer,
                "score": score,
                "accuracy": accuracy_from_score(score),
                "attempt_count": int(answer.get("attempt_count", 1) or 1),
            }
        )
    return evaluated


def accuracy_from_score(score: float) -> float:
    bounded = max(0.0, min(100.0, float(score)))
    return round(bounded / 100.0, 4)


def build_adaptive_rows(*, answers: list[object], questions_by_id: dict[int, object]) -> list[dict]:
    adaptive_rows: list[dict] = []
    for answer in answers:
        question = questions_by_id.get(int(answer.question_id))
        if question is None:
            continue
        adaptive_rows.append(
            {
                "topic_id": int(question.topic_id),
                "difficulty": int(getattr(question, "difficulty", 2) or 2),
                "accuracy": float(getattr(answer, "accuracy", accuracy_from_score(float(answer.score)))),
                "time_taken": float(answer.time_taken),
                "attempt_count": int(getattr(answer, "attempt_count", 1) or 1),
            }
        )
    return adaptive_rows
