import asyncio

from app.core.feature_flags import FeatureFlagService


class _Cache:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, ttl=60):
        self.values[key] = value

    async def delete(self, key):
        self.values.pop(key, None)


class _Session:
    async def execute(self, _stmt):
        class _Result:
            def scalar_one_or_none(self):
                return None

        return _Result()

    async def commit(self):
        return None


def test_feature_flag_rollout_hashes_subject():
    async def _run():
        service = FeatureFlagService(_Session())
        service.cache_service = _Cache()
        await service.cache_service.set(
            service._cache_key("ai_mentor_enabled", 1),
            {
                "enabled": True,
                "rollout_percentage": 0,
                "audience_filter_json": "{}",
                "experiment_key": None,
            },
        )
        disabled = await service.is_enabled("ai_mentor_enabled", 1, subject_id=42)
        assert disabled is False

    asyncio.run(_run())
