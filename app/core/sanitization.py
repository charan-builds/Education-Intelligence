from __future__ import annotations

import html
import re


CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def sanitize_text(value: str, *, max_length: int | None = None) -> str:
    cleaned = CONTROL_CHARS.sub("", value).strip()
    escaped = html.escape(cleaned, quote=True)
    if max_length is not None:
        return escaped[:max_length]
    return escaped
