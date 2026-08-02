from __future__ import annotations


def normalize_answer(value: str) -> str:
    return "".join(ch.lower() for ch in value.strip() if ch.isalnum() or ch.isspace()).strip()


def _accepted_answer_values(question: object) -> list[str]:
    values = getattr(question, "accepted_answers", None) or []
    accepted_values: list[str] = []
    if isinstance(values, str):
        accepted_values.append(values)
    elif isinstance(values, (list, tuple, set)):
        accepted_values.extend(str(value) for value in values if value is not None)

    for option in getattr(question, "options", None) or []:
        if not isinstance(option, dict) or not option.get("is_correct"):
            continue
        for key in ("key", "text", "option_key", "option_text"):
            value = option.get(key)
            if value is not None:
                accepted_values.append(str(value))
    return accepted_values


def evaluate_answers(answers: list[dict], questions_by_id: dict[int, object]) -> list[dict]:
    evaluated: list[dict] = []
    for answer in answers:
        question = questions_by_id.get(int(answer["question_id"]))
        if question is None:
            continue
        normalized_expected = normalize_answer(str(getattr(question, "correct_answer", "") or ""))
        normalized_user = normalize_answer(str(answer.get("user_answer", "") or ""))
        valid_answers = {normalized_expected} if normalized_expected else set()
        for alias in _accepted_answer_values(question):
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


def difficulty_weight(value: object) -> int:
    """Map diagnostic difficulty to the scoring weight."""
    if isinstance(value, dict):
        candidates = (
            value.get("difficulty_weight"),
            value.get("difficulty_level"),
            value.get("difficulty"),
            value.get("difficulty_label"),
        )
    else:
        candidates = (
            getattr(value, "difficulty_weight", None),
            getattr(value, "difficulty_level", None),
            getattr(value, "difficulty", None),
            getattr(value, "difficulty_label", None),
        )

    for candidate in candidates:
        if candidate is None:
            continue
        normalized = str(candidate.value if hasattr(candidate, "value") else candidate).strip().lower()
        if normalized in {"1", "easy"}:
            return 1
        if normalized in {"2", "medium"}:
            return 2
        if normalized in {"3", "hard"}:
            return 3
    return 2


def weighted_score(results: list[dict]) -> float:
    total_weight = 0
    correct_weight = 0
    for item in results:
        weight = difficulty_weight(item)
        total_weight += weight
        is_correct = item.get("is_correct")
        if is_correct is None:
            is_correct = float(item.get("score", 0.0)) >= 100.0
        if is_correct:
            correct_weight += weight
    if total_weight <= 0:
        return 0.0
    return round((correct_weight / total_weight) * 100.0, 2)


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
