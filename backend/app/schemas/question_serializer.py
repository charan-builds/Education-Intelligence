from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any


SENSITIVE_QUESTION_FIELDS = frozenset(
    {
        "accepted_answers",
        "correct_answer",
        "explanation",
        "is_correct",
    }
)

PUBLIC_QUESTION_FIELDS = (
    "test_id",
    "id",
    "version",
    "is_active",
    "topic_id",
    "topic_name",
    "difficulty",
    "difficulty_level",
    "difficulty_label",
    "adaptive_strategy",
    "target_topic_id",
    "target_difficulty",
    "weakness_topic_ids",
    "question_type",
    "question_text",
)

_MISSING = object()
_DIFFICULTY_LABELS_BY_LEVEL = {1: "easy", 2: "medium", 3: "hard"}
_DIFFICULTY_LEVELS_BY_LABEL = {label: level for level, label in _DIFFICULTY_LABELS_BY_LEVEL.items()}


def _option_key(index: int) -> str:
    if 0 <= index < 26:
        return chr(ord("A") + index)
    return str(index + 1)


def _read_field(question: object, field: str) -> Any:
    if isinstance(question, Mapping):
        return question.get(field, _MISSING)
    return getattr(question, field, _MISSING)


def _plain_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {
            key: _plain_value(item)
            for key, item in value.items()
            if str(key) not in SENSITIVE_QUESTION_FIELDS
        }
    if isinstance(value, list):
        return [_plain_value(item) for item in value]
    if isinstance(value, tuple):
        return [_plain_value(item) for item in value]
    return value


def normalize_difficulty_payload(
    difficulty: Any = _MISSING,
    *,
    level: Any = _MISSING,
    label: Any = _MISSING,
) -> tuple[int, str]:
    source = level if level is not _MISSING and level is not None else _MISSING
    if source is _MISSING:
        source = label if label is not _MISSING and label is not None else _MISSING
    if source is _MISSING:
        source = difficulty
    if source is _MISSING or source is None:
        return 2, "medium"

    normalized = str(_plain_value(source)).strip().lower()
    if normalized.isdigit():
        difficulty_level = max(1, min(3, int(normalized)))
        return difficulty_level, _DIFFICULTY_LABELS_BY_LEVEL[difficulty_level]

    difficulty_label = normalized if normalized in _DIFFICULTY_LEVELS_BY_LABEL else "medium"
    return _DIFFICULTY_LEVELS_BY_LABEL[difficulty_label], difficulty_label


def _option_text(option: object) -> str:
    if isinstance(option, Mapping):
        text = (
            option.get("text")
            or option.get("option_text")
            or option.get("label")
            or option.get("value")
            or ""
        )
    else:
        text = option or ""
    return str(text).strip()


def sanitize_options(options: Sequence[object] | None) -> list[dict[str, str]]:
    if isinstance(options, (str, bytes)):
        options = [options.decode() if isinstance(options, bytes) else options]
    sanitized: list[dict[str, str]] = []
    for index, option in enumerate(options or []):
        key = _option_key(index)
        if isinstance(option, Mapping):
            key = str(option.get("key") or option.get("option_key") or key).strip() or key
        text = _option_text(option)
        if text:
            sanitized.append({"key": key, "text": text})
    return sanitized


def sanitize_answer_options(answer_options: Sequence[object] | None) -> list[str]:
    if isinstance(answer_options, (str, bytes)):
        answer_options = [answer_options.decode() if isinstance(answer_options, bytes) else answer_options]
    return [text for option in (answer_options or []) if (text := _option_text(option))]


def sanitize_question(question: object) -> dict[str, Any]:
    """Return an API-safe copy of a question without answer metadata."""
    sanitized: dict[str, Any] = {}

    for field in PUBLIC_QUESTION_FIELDS:
        value = _read_field(question, field)
        if value is _MISSING:
            continue
        sanitized[field] = _plain_value(value)

    has_legacy_difficulty = "difficulty" in sanitized
    if any(field in sanitized for field in ("difficulty", "difficulty_level", "difficulty_label")):
        difficulty_level, difficulty_label = normalize_difficulty_payload(
            sanitized.get("difficulty", _MISSING),
            level=sanitized.get("difficulty_level", _MISSING),
            label=sanitized.get("difficulty_label", _MISSING),
        )
        sanitized["difficulty_level"] = difficulty_level
        sanitized["difficulty_label"] = difficulty_label
        if has_legacy_difficulty:
            sanitized["difficulty"] = difficulty_level

    options = _read_field(question, "options")
    answer_options = _read_field(question, "answer_options")

    if options is not _MISSING and options is not None:
        sanitized["options"] = sanitize_options(options)
    elif answer_options is not _MISSING and answer_options is not None:
        sanitized["options"] = sanitize_options(answer_options)

    if answer_options is not _MISSING and answer_options is not None:
        sanitized["answer_options"] = sanitize_answer_options(answer_options)

    return sanitized
