from __future__ import annotations

import os
import sys
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
    def limit(self, _limit: str, key_func: Callable[[Request], str] | None = None):
        def _decorator(func):
            return func

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
    return get_remote_address(request)


def rate_limit_key_by_user(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        authorization = request.headers.get("authorization", "").strip()
        if authorization:
            return f"auth:{authorization[:48]}"
        return get_remote_address(request)

    tenant_id = getattr(user, "tenant_id", "none")
    user_id = getattr(user, "id", "none")
    return f"tenant:{tenant_id}:user:{user_id}"


def register_rate_limiter(app: FastAPI) -> None:
    if Limiter is None:
        return
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
