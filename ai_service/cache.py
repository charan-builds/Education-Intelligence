from __future__ import annotations

import hashlib
import json
import time
from typing import Any


class TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    @staticmethod
    def make_key(namespace: str, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=True)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"{namespace}:{digest}"

    def get(self, key: str) -> Any | None:
        value = self._store.get(key)
        if value is None:
            return None
        expires_at, payload = value
        if time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return payload

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._store[key] = (time.monotonic() + ttl, value)
