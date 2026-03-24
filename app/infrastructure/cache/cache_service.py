import json
from typing import Any

from app.core.logging import get_logger
from app.core.metrics import cache_operations_total
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
                cache_operations_total.labels(operation="get", result="miss").inc()
                return None
            cache_operations_total.labels(operation="get", result="hit").inc()
            return json.loads(value)
        except Exception as exc:  # fail open
            cache_operations_total.labels(operation="get", result="error").inc()
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
            cache_operations_total.labels(operation="set", result="ok").inc()
            return True
        except Exception as exc:  # fail open
            cache_operations_total.labels(operation="set", result="error").inc()
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
            cache_operations_total.labels(operation="delete", result="ok").inc()
            return True
        except Exception as exc:  # fail open
            cache_operations_total.labels(operation="delete", result="error").inc()
            self.logger.warning(
                "cache delete failed",
                extra={"log_data": {"cache_key": key, "error_type": type(exc).__name__}},
            )
            return False

    async def delete_prefix(self, prefix: str) -> int:
        if self.redis is None:
            return 0
        try:
            deleted = 0
            async for key in self.redis.scan_iter(match=f"{prefix}*"):
                deleted += int(await self.redis.delete(key))
            cache_operations_total.labels(operation="delete_prefix", result="ok").inc()
            return deleted
        except Exception as exc:  # fail open
            cache_operations_total.labels(operation="delete_prefix", result="error").inc()
            self.logger.warning(
                "cache delete prefix failed",
                extra={"log_data": {"cache_prefix": prefix, "error_type": type(exc).__name__}},
            )
            return 0

    @staticmethod
    def build_key(namespace: str, **parts: Any) -> str:
        normalized = ":".join(f"{name}={parts[name]}" for name in sorted(parts))
        return f"{namespace}:{normalized}" if normalized else namespace

    async def get_or_set(self, key: str, *, ttl: int, factory) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        await self.set(key, value, ttl=ttl)
        return value
