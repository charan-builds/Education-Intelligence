import json
from uuid import uuid4
from typing import Any

from app.core.logging import get_logger
from app.core.metrics import cache_operations_total
from app.infrastructure.cache.redis_client import get_redis_client


class CacheService:
    def __init__(self) -> None:
        self.redis = get_redis_client()
        self.logger = get_logger()

    async def _namespace_version(self, namespace: str) -> int:
        if self.redis is None:
            return 1
        raw = await self.redis.get(f"cache-version:{namespace}")
        try:
            return int(raw) if raw is not None else 1
        except (TypeError, ValueError):
            return 1

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
            self.redis = None
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
            self.redis = None
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
            self.redis = None
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
            self.redis = None
            return 0

    @staticmethod
    def build_key(namespace: str, **parts: Any) -> str:
        normalized = ":".join(f"{name}={parts[name]}" for name in sorted(parts))
        return f"{namespace}:{normalized}" if normalized else namespace

    async def build_tenant_versioned_key(self, namespace: str, *, tenant_id: int, **parts: Any) -> str:
        scoped_namespace = f"{namespace}:tenant:{tenant_id}"
        return await self.build_versioned_key(scoped_namespace, tenant_id=tenant_id, **parts)

    async def build_versioned_key(self, namespace: str, **parts: Any) -> str:
        version = await self._namespace_version(namespace)
        return self.build_key(namespace, version=version, **parts)

    async def namespace_version(self, namespace: str) -> int:
        return await self._namespace_version(namespace)

    async def bump_namespace_version(self, namespace: str) -> int:
        if self.redis is None:
            return 1
        key = f"cache-version:{namespace}"
        try:
            version = int(await self.redis.incr(key))
            cache_operations_total.labels(operation="version_bump", result="ok").inc()
            return version
        except Exception as exc:  # fail open
            cache_operations_total.labels(operation="version_bump", result="error").inc()
            self.logger.warning(
                "cache version bump failed",
                extra={"log_data": {"cache_namespace": namespace, "error_type": type(exc).__name__}},
            )
            self.redis = None
            return 1

    async def get_or_set(self, key: str, *, ttl: int, factory) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        await self.set(key, value, ttl=ttl)
        return value

    async def acquire_lock(self, key: str, *, ttl: int) -> str | None:
        if self.redis is None:
            return "lock-unavailable"
        token = uuid4().hex
        try:
            acquired = await self.redis.set(key, token, ex=ttl, nx=True)
            if acquired:
                cache_operations_total.labels(operation="lock_acquire", result="ok").inc()
                return token
            cache_operations_total.labels(operation="lock_acquire", result="busy").inc()
            return None
        except Exception as exc:  # fail open
            cache_operations_total.labels(operation="lock_acquire", result="error").inc()
            self.logger.warning(
                "cache lock acquire failed",
                extra={"log_data": {"cache_key": key, "error_type": type(exc).__name__}},
            )
            self.redis = None
            return "lock-unavailable"

    async def release_lock(self, key: str, token: str | None = None) -> bool:
        if self.redis is None:
            return False
        try:
            if token and token != "lock-unavailable":
                current = await self.redis.get(key)
                if current != token:
                    cache_operations_total.labels(operation="lock_release", result="skipped").inc()
                    return False
            await self.redis.delete(key)
            cache_operations_total.labels(operation="lock_release", result="ok").inc()
            return True
        except Exception as exc:  # fail open
            cache_operations_total.labels(operation="lock_release", result="error").inc()
            self.logger.warning(
                "cache lock release failed",
                extra={"log_data": {"cache_key": key, "error_type": type(exc).__name__}},
            )
            self.redis = None
            return False

    async def increment_counter(self, key: str, *, ttl: int | None = None) -> int:
        if self.redis is None:
            return 0
        try:
            value = int(await self.redis.incr(key))
            if ttl is not None and value == 1:
                await self.redis.expire(key, ttl)
            cache_operations_total.labels(operation="counter_increment", result="ok").inc()
            return value
        except Exception as exc:  # fail open
            cache_operations_total.labels(operation="counter_increment", result="error").inc()
            self.logger.warning(
                "cache counter increment failed",
                extra={"log_data": {"cache_key": key, "error_type": type(exc).__name__}},
            )
            self.redis = None
            return 0

    async def decrement_counter(self, key: str) -> int:
        if self.redis is None:
            return 0
        try:
            value = int(await self.redis.decr(key))
            if value <= 0:
                await self.redis.delete(key)
                value = 0
            cache_operations_total.labels(operation="counter_decrement", result="ok").inc()
            return value
        except Exception as exc:  # fail open
            cache_operations_total.labels(operation="counter_decrement", result="error").inc()
            self.logger.warning(
                "cache counter decrement failed",
                extra={"log_data": {"cache_key": key, "error_type": type(exc).__name__}},
            )
            self.redis = None
            return 0

    async def get_counter(self, key: str) -> int:
        if self.redis is None:
            return 0
        try:
            raw = await self.redis.get(key)
            cache_operations_total.labels(operation="counter_get", result="ok").inc()
            return int(raw) if raw is not None else 0
        except Exception as exc:  # fail open
            cache_operations_total.labels(operation="counter_get", result="error").inc()
            self.logger.warning(
                "cache counter get failed",
                extra={"log_data": {"cache_key": key, "error_type": type(exc).__name__}},
            )
            self.redis = None
            return 0
