import asyncio
from types import SimpleNamespace

from app.presentation import gamification_routes


class _StubGamificationService:
    def __init__(self, _db):
        self.db = _db

    async def get_profile(self, *, tenant_id: int, user_id: int):
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "level": 3,
            "total_xp": 540,
            "current_level_xp": 140,
            "xp_to_next_level": 300,
            "current_streak_days": 5,
            "longest_streak_days": 8,
            "completed_topics_count": 7,
            "completed_tests_count": 2,
            "last_activity_on": "2026-03-29",
            "recent_events": [],
        }

    async def get_leaderboard(self, *, tenant_id: int, current_user_id: int, limit: int = 10):
        return {
            "tenant_id": tenant_id,
            "generated_at": "2026-03-29T00:00:00Z",
            "entries": [
                {
                    "rank": 1,
                    "user_id": current_user_id,
                    "display_name": "Alex",
                    "level": 3,
                    "total_xp": 540,
                    "current_streak_days": 5,
                    "completed_topics_count": 7,
                    "completed_tests_count": 2,
                    "is_current_user": True,
                }
            ][:limit],
        }

    async def recent_activity(self, *, tenant_id: int, user_id: int, limit: int = 20):
        _ = tenant_id, user_id
        return [
            {
                "id": 1,
                "event_type": "topic_completed",
                "source_type": "roadmap_step",
                "source_id": 44,
                "topic_id": 12,
                "diagnostic_test_id": None,
                "xp_delta": 25,
                "level_after": 3,
                "streak_after": 5,
                "awarded_at": "2026-03-29T00:00:00Z",
            }
        ][:limit]


def test_gamification_me(monkeypatch):
    monkeypatch.setattr(gamification_routes, "GamificationService", _StubGamificationService)

    async def _run():
        response = await gamification_routes.gamification_me(
            db=object(),
            current_user=SimpleNamespace(id=7, tenant_id=3),
        )
        assert response["level"] == 3
        assert response["total_xp"] == 540

    asyncio.run(_run())


def test_gamification_leaderboard(monkeypatch):
    monkeypatch.setattr(gamification_routes, "GamificationService", _StubGamificationService)

    async def _run():
        response = await gamification_routes.gamification_leaderboard(
            limit=10,
            db=object(),
            current_user=SimpleNamespace(id=7, tenant_id=3),
        )
        assert response["entries"][0]["is_current_user"] is True
        assert response["entries"][0]["total_xp"] == 540

    asyncio.run(_run())


def test_gamification_activity(monkeypatch):
    monkeypatch.setattr(gamification_routes, "GamificationService", _StubGamificationService)

    async def _run():
        response = await gamification_routes.gamification_activity(
            limit=5,
            db=object(),
            current_user=SimpleNamespace(id=7, tenant_id=3),
        )
        assert response[0]["event_type"] == "topic_completed"
        assert response[0]["xp_delta"] == 25

    asyncio.run(_run())
