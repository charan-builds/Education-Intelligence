from functools import lru_cache
from typing import Any

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> Any:
    settings = get_settings()
    try:
        from redis.asyncio import Redis
    except Exception:  # pragma: no cover
        return None
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=0.25,
        socket_timeout=0.25,
        retry_on_timeout=False,
        health_check_interval=30,
    )
