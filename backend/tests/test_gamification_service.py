import asyncio
from datetime import date
from types import SimpleNamespace

from app.application.services.gamification_service import GamificationService


class _FakeSession:
    def __init__(self):
        self.users = {}
        self.recent_events = []

    async def get(self, model, user_id):
        _ = model
        return self.users.get(user_id)

    async def flush(self):
        return None

    async def execute(self, stmt):
        _ = stmt
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: list(self.recent_events)), all=lambda: [])


class _FakeProfileRepository:
    def __init__(self, profile):
        self.profile = profile

    async def get_or_create(self, **kwargs):
        _ = kwargs
        return self.profile


class _FakeEventRepository:
    def __init__(self):
        self.existing = {}
        self.created = []

    async def get_by_idempotency_key(self, *, tenant_id: int, user_id: int, idempotency_key: str):
        _ = tenant_id, user_id
        return self.existing.get(idempotency_key)

    async def create(self, **kwargs):
        event = SimpleNamespace(
            id=len(self.created) + 1,
            event_type=kwargs["event_type"],
            source_type=kwargs["source_type"],
            source_id=kwargs["source_id"],
            topic_id=kwargs.get("topic_id"),
            diagnostic_test_id=kwargs.get("diagnostic_test_id"),
            xp_delta=kwargs["xp_delta"],
            level_after=kwargs["level_after"],
            streak_after=kwargs["streak_after"],
            awarded_at=kwargs["awarded_at"],
        )
        self.created.append(event)
        self.existing[kwargs["idempotency_key"]] = event
        return event


def test_award_topic_completion_updates_profile_and_user():
    async def _run():
        session = _FakeSession()
        session.users[7] = SimpleNamespace(tenant_id=3, experience_points=0, current_streak_days=0, focus_score=0.0)
        profile = SimpleNamespace(
            tenant_id=3,
            user_id=7,
            level=1,
            total_xp=190,
            current_level_xp=190,
            xp_to_next_level=200,
            current_streak_days=2,
            longest_streak_days=2,
            last_activity_on=date(2026, 3, 28),
            completed_topics_count=1,
            completed_tests_count=0,
            created_at=None,
            updated_at=None,
        )
        service = GamificationService(session)
        service.profile_repository = _FakeProfileRepository(profile)
        service.event_repository = _FakeEventRepository()

        result = await service.award_topic_completion(
            tenant_id=3,
            user_id=7,
            topic_id=19,
            roadmap_step_id=44,
        )

        assert result["level"] == 2
        assert result["total_xp"] == 215
        assert result["current_streak_days"] == 3
        assert result["completed_topics_count"] == 2
        assert session.users[7].experience_points == 215
        assert session.users[7].current_streak_days == 3
        assert service.event_repository.created[0].xp_delta == 25

    asyncio.run(_run())


def test_award_test_completion_is_idempotent():
    async def _run():
        session = _FakeSession()
        session.users[9] = SimpleNamespace(tenant_id=5, experience_points=80, current_streak_days=1, focus_score=0.0)
        profile = SimpleNamespace(
            tenant_id=5,
            user_id=9,
            level=1,
            total_xp=80,
            current_level_xp=80,
            xp_to_next_level=200,
            current_streak_days=1,
            longest_streak_days=1,
            last_activity_on=date(2026, 3, 29),
            completed_topics_count=0,
            completed_tests_count=0,
            created_at=None,
            updated_at=None,
        )
        event_repo = _FakeEventRepository()
        service = GamificationService(session)
        service.profile_repository = _FakeProfileRepository(profile)
        service.event_repository = event_repo

        first = await service.award_test_completion(
            tenant_id=5,
            user_id=9,
            diagnostic_test_id=77,
            goal_id=11,
        )
        second = await service.award_test_completion(
            tenant_id=5,
            user_id=9,
            diagnostic_test_id=77,
            goal_id=11,
        )

        assert first["total_xp"] == 120
        assert second["total_xp"] == 120
        assert len(event_repo.created) == 1
        assert profile.completed_tests_count == 1

    asyncio.run(_run())
