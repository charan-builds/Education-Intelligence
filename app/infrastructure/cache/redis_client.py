from functools import lru_cache
from typing import Any

from app.core.config import get_settings

try:
    from redis.asyncio import Redis
except Exception:  # pragma: no cover
    Redis = None  # type: ignore


@lru_cache
def get_redis_client() -> Any:
    settings = get_settings()
    if Redis is None:
        return None
    return Redis.from_url(settings.redis_url, decode_responses=True)
