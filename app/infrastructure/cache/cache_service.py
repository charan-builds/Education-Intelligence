import json
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.cache.redis_client import get_redis_client


class CacheService:
    def __init__(self) -> None:
        self.redis = get_redis_client()
        self.logger = get_logger()

    async def get(self, key: str) -> Any | None:
        if self.redis is None:
            return None
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as exc:  # fail open
            self.logger.warning(
                "cache get failed",
                extra={"log_data": {"cache_key": key, "error_type": type(exc).__name__}},
            )
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if self.redis is None:
            return False
        try:
            await self.redis.set(key, json.dumps(value, default=str), ex=ttl)
            return True
        except Exception as exc:  # fail open
            self.logger.warning(
                "cache set failed",
                extra={"log_data": {"cache_key": key, "error_type": type(exc).__name__}},
            )
            return False

    async def delete(self, key: str) -> bool:
        if self.redis is None:
            return False
        try:
            await self.redis.delete(key)
            return True
        except Exception as exc:  # fail open
            self.logger.warning(
                "cache delete failed",
                extra={"log_data": {"cache_key": key, "error_type": type(exc).__name__}},
            )
            return False
