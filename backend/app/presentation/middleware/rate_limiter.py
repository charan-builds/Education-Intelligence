from __future__ import annotations

import os
import sys
import time
from collections import defaultdict, deque
from typing import Any, Callable

from fastapi import FastAPI, Request
from app.core.config import get_settings

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address
except Exception:  # pragma: no cover
    Limiter = None  # type: ignore
    RateLimitExceeded = Exception  # type: ignore
    SlowAPIMiddleware = None  # type: ignore

    def _rate_limit_exceeded_handler(*args, **kwargs):
        return None

    def get_remote_address(request: Request) -> str:
        return request.client.host if request.client else "unknown"


class _NoopLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def limit(self, limit_value: str, key_func: Callable[[Request], str] | None = None):
        amount_raw, window_raw = limit_value.split("/", 1)
        max_hits = int(amount_raw)
        window_seconds = 60 if window_raw.startswith("min") else 1

        def _decorator(func):
            async def _wrapped(*args, **kwargs):
                request = kwargs.get("request")
                if request is None:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                if request is not None:
                    resolved_key = key_func(request) if key_func else get_remote_address(request)
                    bucket_key = f"{func.__module__}.{func.__name__}:{resolved_key}:{limit_value}"
                    now = time.monotonic()
                    bucket = self._buckets[bucket_key]
                    while bucket and bucket[0] <= now - window_seconds:
                        bucket.popleft()
                    if len(bucket) >= max_hits:
                        raise RateLimitExceeded(detail=f"Rate limit exceeded: {limit_value}")  # type: ignore[arg-type]
                    bucket.append(now)
                return await func(*args, **kwargs)

            return _wrapped

        return _decorator


def _running_under_pytest() -> bool:
    return "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))


if Limiter is None or _running_under_pytest():
    limiter: Any = _NoopLimiter()
else:
    settings = get_settings()
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[],
        storage_uri=settings.rate_limit_storage_url or settings.redis_url,
    )


def rate_limit_key_by_ip(request: Request) -> str:
    try:
        return get_remote_address(request)
    except Exception:
        client = getattr(request, "client", None)
        host = getattr(client, "host", None)
        return str(host or "unknown")


def rate_limit_key_by_user(request: Request) -> str:
    state = getattr(request, "state", None)
    user = getattr(state, "user", None)
    if user is None:
        headers = getattr(request, "headers", {}) or {}
        authorization = str(headers.get("authorization", "")).strip() if hasattr(headers, "get") else ""
        if authorization:
            return f"auth:{authorization[:48]}"
        return rate_limit_key_by_ip(request)

    tenant_id = getattr(user, "tenant_id", "none")
    user_id = getattr(user, "id", "none")
    return f"tenant:{tenant_id}:user:{user_id}"


def register_rate_limiter(app: FastAPI) -> None:
    if Limiter is None:
        return
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
