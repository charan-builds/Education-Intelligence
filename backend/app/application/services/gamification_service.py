from datetime import date, datetime, timezone

from sqlalchemy import case, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import NotFoundError
from app.domain.models.gamification_event import GamificationEvent
from app.domain.models.gamification_profile import GamificationProfile
from app.domain.models.user import User
from app.infrastructure.repositories.gamification_event_repository import GamificationEventRepository
from app.infrastructure.repositories.gamification_profile_repository import GamificationProfileRepository


class GamificationService:
    TOPIC_COMPLETION_XP = 25
    TEST_COMPLETION_XP = 40
    BASE_LEVEL_XP = 200
    LEVEL_XP_GROWTH = 50

    def __init__(self, session: AsyncSession):
        self.session = session
        self.profile_repository = GamificationProfileRepository(session)
        self.event_repository = GamificationEventRepository(session)

    def _xp_required_for_level(self, level: int) -> int:
        return self.BASE_LEVEL_XP + max(level - 1, 0) * self.LEVEL_XP_GROWTH

    def _resolve_level_state(self, total_xp: int) -> tuple[int, int, int]:
        level = 1
        remaining_xp = max(int(total_xp), 0)
        xp_for_level = self._xp_required_for_level(level)
        while remaining_xp >= xp_for_level:
            remaining_xp -= xp_for_level
            level += 1
            xp_for_level = self._xp_required_for_level(level)
        return level, remaining_xp, xp_for_level

    def _compute_streak(self, *, current_streak_days: int, last_activity_on: date | None, activity_day: date) -> int:
        if last_activity_on is None:
            return 1
        gap = (activity_day - last_activity_on).days
        if gap <= 0:
            return max(1, current_streak_days)
        if gap == 1:
            return max(1, current_streak_days) + 1
        return 1

    async def _get_user(self, *, tenant_id: int, user_id: int) -> User:
        user = await self.session.get(User, user_id)
        if user is None or int(user.tenant_id) != int(tenant_id):
            raise NotFoundError("User not found")
        return user

    async def _apply_activity(
        self,
        *,
        tenant_id: int,
        user_id: int,
        event_type: str,
        source_type: str,
        source_id: int,
        xp_delta: int,
        idempotency_key: str,
        topic_id: int | None = None,
        diagnostic_test_id: int | None = None,
        metadata: dict | None = None,
        activity_time: datetime | None = None,
    ) -> dict:
        existing = await self.event_repository.get_by_idempotency_key(
            tenant_id=tenant_id,
            user_id=user_id,
            idempotency_key=idempotency_key,
        )
        profile = await self.profile_repository.get_or_create(tenant_id=tenant_id, user_id=user_id, for_update=True)
        if existing is not None:
            return self._serialize_profile(profile, recent_events=[existing])

        user = await self._get_user(tenant_id=tenant_id, user_id=user_id)
        event_time = activity_time or datetime.now(timezone.utc)
        activity_day = event_time.date()

        profile.current_streak_days = self._compute_streak(
            current_streak_days=int(profile.current_streak_days or 0),
            last_activity_on=profile.last_activity_on,
            activity_day=activity_day,
        )
        profile.longest_streak_days = max(int(profile.longest_streak_days or 0), int(profile.current_streak_days or 0))
        profile.last_activity_on = activity_day
        profile.total_xp = int(profile.total_xp or 0) + int(xp_delta)
        level, current_level_xp, xp_to_next_level = self._resolve_level_state(int(profile.total_xp or 0))
        profile.level = level
        profile.current_level_xp = current_level_xp
        profile.xp_to_next_level = xp_to_next_level
        if event_type == "topic_completed":
            profile.completed_topics_count = int(profile.completed_topics_count or 0) + 1
        if event_type == "test_completed":
            profile.completed_tests_count = int(profile.completed_tests_count or 0) + 1
        profile.updated_at = event_time

        user.experience_points = int(profile.total_xp or 0)
        user.current_streak_days = int(profile.current_streak_days or 0)
        user.focus_score = round(
            min(
                100.0,
                35.0
                + min(int(user.current_streak_days or 0), 14) * 3.5
                + min(int(user.experience_points or 0) / 25.0, 30.0),
            ),
            2,
        )

        event = await self.event_repository.create(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            source_type=source_type,
            source_id=source_id,
            topic_id=topic_id,
            diagnostic_test_id=diagnostic_test_id,
            xp_delta=xp_delta,
            level_after=int(profile.level or 1),
            streak_after=int(profile.current_streak_days or 0),
            idempotency_key=idempotency_key,
            metadata=metadata,
            awarded_at=event_time,
        )
        await self.session.flush()
        return self._serialize_profile(profile, recent_events=[event])

    def _serialize_event(self, event: GamificationEvent) -> dict:
        return {
            "id": int(event.id),
            "event_type": str(event.event_type),
            "source_type": str(event.source_type),
            "source_id": int(event.source_id),
            "topic_id": int(event.topic_id) if event.topic_id is not None else None,
            "diagnostic_test_id": int(event.diagnostic_test_id) if event.diagnostic_test_id is not None else None,
            "xp_delta": int(event.xp_delta or 0),
            "level_after": int(event.level_after or 1),
            "streak_after": int(event.streak_after or 0),
            "awarded_at": event.awarded_at.isoformat(),
        }

    def _serialize_profile(self, profile: GamificationProfile, *, recent_events: list[GamificationEvent]) -> dict:
        return {
            "tenant_id": int(profile.tenant_id),
            "user_id": int(profile.user_id),
            "level": int(profile.level or 1),
            "total_xp": int(profile.total_xp or 0),
            "current_level_xp": int(profile.current_level_xp or 0),
            "xp_to_next_level": int(profile.xp_to_next_level or self.BASE_LEVEL_XP),
            "current_streak_days": int(profile.current_streak_days or 0),
            "longest_streak_days": int(profile.longest_streak_days or 0),
            "completed_topics_count": int(profile.completed_topics_count or 0),
            "completed_tests_count": int(profile.completed_tests_count or 0),
            "last_activity_on": profile.last_activity_on.isoformat() if profile.last_activity_on is not None else None,
            "recent_events": [self._serialize_event(event) for event in recent_events],
        }

    async def award_topic_completion(
        self,
        *,
        tenant_id: int,
        user_id: int,
        topic_id: int,
        roadmap_step_id: int,
        activity_time: datetime | None = None,
    ) -> dict:
        return await self._apply_activity(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="topic_completed",
            source_type="roadmap_step",
            source_id=roadmap_step_id,
            topic_id=topic_id,
            xp_delta=self.TOPIC_COMPLETION_XP,
            idempotency_key=f"gamification:topic-completed:{tenant_id}:{user_id}:{roadmap_step_id}",
            metadata={"topic_id": topic_id, "roadmap_step_id": roadmap_step_id},
            activity_time=activity_time,
        )

    async def award_test_completion(
        self,
        *,
        tenant_id: int,
        user_id: int,
        diagnostic_test_id: int,
        goal_id: int | None = None,
        activity_time: datetime | None = None,
    ) -> dict:
        return await self._apply_activity(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="test_completed",
            source_type="diagnostic_test",
            source_id=diagnostic_test_id,
            diagnostic_test_id=diagnostic_test_id,
            xp_delta=self.TEST_COMPLETION_XP,
            idempotency_key=f"gamification:test-completed:{tenant_id}:{user_id}:{diagnostic_test_id}",
            metadata={"goal_id": goal_id} if goal_id is not None else {},
            activity_time=activity_time,
        )

    async def get_profile(self, *, tenant_id: int, user_id: int) -> dict:
        profile = await self.profile_repository.get_or_create(tenant_id=tenant_id, user_id=user_id)
        recent_result = await self.session.execute(
            select(GamificationEvent)
            .where(
                GamificationEvent.tenant_id == tenant_id,
                GamificationEvent.user_id == user_id,
            )
            .order_by(GamificationEvent.awarded_at.desc(), GamificationEvent.id.desc())
            .limit(10)
        )
        return self._serialize_profile(profile, recent_events=list(recent_result.scalars().all()))

    async def get_leaderboard(self, *, tenant_id: int, current_user_id: int, limit: int = 10) -> dict:
        safe_limit = max(1, min(int(limit), 100))
        name_expr = case(
            (User.display_name.is_not(None), User.display_name),
            else_=User.email,
        )
        result = await self.session.execute(
            select(
                GamificationProfile.user_id,
                name_expr.label("display_name"),
                GamificationProfile.level,
                GamificationProfile.total_xp,
                GamificationProfile.current_streak_days,
                GamificationProfile.completed_topics_count,
                GamificationProfile.completed_tests_count,
            )
            .join(User, User.id == GamificationProfile.user_id)
            .where(GamificationProfile.tenant_id == tenant_id)
            .order_by(
                desc(GamificationProfile.total_xp),
                desc(GamificationProfile.current_streak_days),
                desc(GamificationProfile.completed_topics_count),
                GamificationProfile.user_id.asc(),
            )
            .limit(safe_limit)
        )
        entries = []
        for rank, row in enumerate(result.all(), start=1):
            entries.append(
                {
                    "rank": rank,
                    "user_id": int(row.user_id),
                    "display_name": str(row.display_name),
                    "level": int(row.level or 1),
                    "total_xp": int(row.total_xp or 0),
                    "current_streak_days": int(row.current_streak_days or 0),
                    "completed_topics_count": int(row.completed_topics_count or 0),
                    "completed_tests_count": int(row.completed_tests_count or 0),
                    "is_current_user": int(row.user_id) == int(current_user_id),
                }
            )
        return {
            "tenant_id": tenant_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entries": entries,
        }

    async def recent_activity(self, *, tenant_id: int, user_id: int, limit: int = 20) -> list[dict]:
        safe_limit = max(1, min(int(limit), 100))
        result = await self.session.execute(
            select(GamificationEvent)
            .where(
                GamificationEvent.tenant_id == tenant_id,
                GamificationEvent.user_id == user_id,
            )
            .order_by(GamificationEvent.awarded_at.desc(), GamificationEvent.id.desc())
            .limit(safe_limit)
        )
        return [self._serialize_event(event) for event in result.scalars().all()]
