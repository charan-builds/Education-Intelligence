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
