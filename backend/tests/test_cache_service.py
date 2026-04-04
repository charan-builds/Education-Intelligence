import asyncio

from app.infrastructure.cache.cache_service import CacheService


class _Logger:
    def warning(self, *args, **kwargs):
        return None


def test_cache_service_no_redis_fails_open():
    async def _run():
        service = CacheService()
        service.redis = None
        service.logger = _Logger()

        assert await service.get("k") is None
        assert await service.set("k", {"v": 1}, ttl=10) is False
        assert await service.delete("k") is False

    asyncio.run(_run())


def test_cache_service_lock_round_trip():
    class _Redis:
        def __init__(self):
            self.values = {}

        async def set(self, key, value, ex=None, nx=False):
            if nx and key in self.values:
                return False
            self.values[key] = value
            return True

        async def get(self, key):
            return self.values.get(key)

        async def delete(self, key):
            self.values.pop(key, None)
            return 1

    async def _run():
        service = CacheService()
        service.redis = _Redis()
        service.logger = _Logger()

        token = await service.acquire_lock("analytics:student:7", ttl=30)
        assert isinstance(token, str)
        assert await service.acquire_lock("analytics:student:7", ttl=30) is None
        assert await service.release_lock("analytics:student:7", token) is True
        assert await service.acquire_lock("analytics:student:7", ttl=30) is not None

    asyncio.run(_run())


def test_cache_service_counter_round_trip():
    class _Redis:
        def __init__(self):
            self.values = {}

        async def incr(self, key):
            self.values[key] = int(self.values.get(key, 0)) + 1
            return self.values[key]

        async def decr(self, key):
            self.values[key] = int(self.values.get(key, 0)) - 1
            return self.values[key]

        async def expire(self, key, ttl):
            _ = key, ttl
            return True

        async def get(self, key):
            return self.values.get(key)

        async def delete(self, key):
            self.values.pop(key, None)
            return 1

    async def _run():
        service = CacheService()
        service.redis = _Redis()
        service.logger = _Logger()

        assert await service.increment_counter("analytics:tenant_jobs:7", ttl=60) == 1
        assert await service.increment_counter("analytics:tenant_jobs:7", ttl=60) == 2
        assert await service.get_counter("analytics:tenant_jobs:7") == 2
        assert await service.decrement_counter("analytics:tenant_jobs:7") == 1
        assert await service.decrement_counter("analytics:tenant_jobs:7") == 0
        assert await service.get_counter("analytics:tenant_jobs:7") == 0

    asyncio.run(_run())
