from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI, Request

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


if Limiter is None:
    limiter: Any = _NoopLimiter()
else:
    limiter = Limiter(key_func=get_remote_address, default_limits=[])


def rate_limit_key_by_ip(request: Request) -> str:
    return get_remote_address(request)


def rate_limit_key_by_user(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
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
