import asyncio

from app.application.services.roadmap_service import RoadmapService


class _Session:
    pass


class _Cache:
    def __init__(self):
        self.payload = {
            "items": [
                {
                    "id": 1,
                    "user_id": 7,
                    "goal_id": 3,
                    "generated_at": "2026-01-01T00:00:00+00:00",
                    "steps": [],
                }
            ],
            "meta": {"total": 1, "limit": 20, "offset": 0, "next_offset": None, "next_cursor": None},
        }

    async def get(self, key):
        return self.payload

    async def set(self, key, value, ttl=300):
        return True


class _RoadmapRepo:
    async def list_user_roadmaps(self, **kwargs):
        raise AssertionError("DB should not be called on cache hit")

    async def count_user_roadmaps(self, **kwargs):
        raise AssertionError("DB should not be called on cache hit")


def test_roadmap_page_returns_cached_payload():
    async def _run():
        service = RoadmapService(_Session())
        service.cache_service = _Cache()
        service.roadmap_repository = _RoadmapRepo()

        result = await service.list_for_user_page(user_id=7, tenant_id=2, limit=20, offset=0)
        assert result["items"][0]["id"] == 1
        assert result["meta"]["total"] == 1

    asyncio.run(_run())
