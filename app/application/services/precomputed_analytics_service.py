from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.outbox_service import OutboxService
from app.core.config import get_settings
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.repositories.analytics_snapshot_repository import AnalyticsSnapshotRepository
from app.domain.models.learning_event import LearningEvent
from app.domain.models.topic_score import TopicScore
from app.domain.models.user import User, UserRole


class PrecomputedAnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = AnalyticsSnapshotRepository(session)
        self.cache = CacheService()

    async def refresh_tenant_dashboard(self, *, tenant_id: int) -> dict:
        now = datetime.now(timezone.utc)
        window_start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        active_learners = int(
            (
                await self.session.execute(
                    select(func.count(User.id)).where(User.tenant_id == tenant_id, User.role == UserRole.student)
                )
            ).scalar_one()
            or 0
        )
        event_count = int(
            (
                await self.session.execute(
                    select(func.count(LearningEvent.id)).where(
                        LearningEvent.tenant_id == tenant_id,
                        func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at) >= window_start,
                    )
                )
            ).scalar_one()
            or 0
        )
        avg_mastery = float(
            (
                await self.session.execute(
                    select(func.avg(TopicScore.score)).where(TopicScore.tenant_id == tenant_id)
                )
            ).scalar_one()
            or 0.0
        )
        payload = {
            "tenant_id": tenant_id,
            "active_learners": active_learners,
            "weekly_event_count": event_count,
            "average_topic_mastery": round(avg_mastery, 2),
        }
        await self.repository.upsert_snapshot(
            tenant_id=tenant_id,
            snapshot_type="tenant_dashboard",
            subject_id=None,
            payload_json=json.dumps(payload, ensure_ascii=True),
            window_start=window_start,
            window_end=now,
            updated_at=now,
        )
        cache_key = await self.cache.build_tenant_versioned_key("analytics:precomputed:tenant-dashboard", tenant_id=tenant_id)
        await self.cache.set(cache_key, payload, ttl=300)
        if get_settings().kafka_enabled:
            await OutboxService(self.session).add_analytics_message(
                tenant_id=tenant_id,
                snapshot_type="tenant_dashboard",
                subject_id=None,
                window_start=window_start.isoformat(),
                window_end=now.isoformat(),
                idempotency_key=f"analytics:{tenant_id}:tenant_dashboard:{window_start.date().isoformat()}",
            )
        return payload

    async def refresh_user_learning_summary(self, *, tenant_id: int, user_id: int) -> dict:
        now = datetime.now(timezone.utc)
        window_start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        event_count = int(
            (
                await self.session.execute(
                    select(func.count(LearningEvent.id)).where(
                        LearningEvent.tenant_id == tenant_id,
                        LearningEvent.user_id == user_id,
                        func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at) >= window_start,
                    )
                )
            ).scalar_one()
            or 0
        )
        avg_score = float(
            (
                await self.session.execute(
                    select(func.avg(TopicScore.score)).where(TopicScore.tenant_id == tenant_id, TopicScore.user_id == user_id)
                )
            ).scalar_one()
            or 0.0
        )
        payload = {"tenant_id": tenant_id, "user_id": user_id, "weekly_event_count": event_count, "average_score": round(avg_score, 2)}
        await self.repository.upsert_snapshot(
            tenant_id=tenant_id,
            snapshot_type="user_learning_summary",
            subject_id=user_id,
            payload_json=json.dumps(payload, ensure_ascii=True),
            window_start=window_start,
            window_end=now,
            updated_at=now,
        )
        if get_settings().kafka_enabled:
            await OutboxService(self.session).add_analytics_message(
                tenant_id=tenant_id,
                snapshot_type="user_learning_summary",
                subject_id=user_id,
                window_start=window_start.isoformat(),
                window_end=now.isoformat(),
                idempotency_key=f"analytics:{tenant_id}:user_learning_summary:{user_id}:{window_start.date().isoformat()}",
            )
        return payload
