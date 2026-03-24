from __future__ import annotations

import re


def sanitize_text(value: str, *, limit: int = 4000) -> str:
    text = value.strip()
    text = text.replace("\x00", "")
    text = re.sub(r"\s+", " ", text)
    return text[:limit]


def safe_topic_name(value: str) -> str:
    return sanitize_text(value, limit=200)


def injection_hints(value: str) -> list[str]:
    lowered = value.lower()
    suspicious_patterns = [
        "ignore previous instructions",
        "system prompt",
        "developer message",
        "reveal prompt",
        "act as",
    ]
    return [pattern for pattern in suspicious_patterns if pattern in lowered]
