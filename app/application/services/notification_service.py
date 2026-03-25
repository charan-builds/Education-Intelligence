from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.mentor_notification_service import MentorNotificationService
from app.application.services.outbox_service import OutboxService
from app.core.config import get_settings
from app.domain.models.learning_event import LearningEvent
from app.domain.models.notification import Notification
from app.domain.models.roadmap import Roadmap
from app.domain.models.roadmap_step import RoadmapStep
from app.domain.models.topic_score import TopicScore
from app.domain.models.user import User, UserRole
from app.domain.models.user_skill_vector import UserSkillVector
from app.infrastructure.repositories.notification_repository import NotificationRepository
from app.realtime.hub import realtime_hub


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = NotificationRepository(session)
        self.mentor_notification_service = MentorNotificationService()

    async def list_for_user(self, *, tenant_id: int, user_id: int, unread_only: bool = False, limit: int = 30) -> list[dict]:
        rows = await self.repository.list_for_user(tenant_id=tenant_id, user_id=user_id, unread_only=unread_only, limit=limit)
        return [self._serialize(row) for row in rows]

    async def mark_read(self, *, tenant_id: int, user_id: int, notification_id: int) -> dict:
        row = await self.repository.get_for_user(tenant_id=tenant_id, user_id=user_id, notification_id=notification_id)
        if row is None:
            raise ValueError("Notification not found")
        if row.read_at is None:
            await self.repository.mark_read(row, read_at=datetime.now(timezone.utc))
            await self.session.commit()
        return self._serialize(row)

    async def create_notification(
        self,
        *,
        tenant_id: int,
        user_id: int,
        notification_type: str,
        severity: str,
        priority: str = "normal",
        title: str,
        message: str,
        metadata: dict | None = None,
        action_url: str | None = None,
        dedupe_window_hours: int = 24,
        dedupe_key: str | None = None,
        scheduled_for: datetime | None = None,
        commit: bool = True,
    ) -> dict | None:
        if dedupe_key:
            duplicate = await self.repository.find_by_dedupe_key(
                tenant_id=tenant_id,
                user_id=user_id,
                dedupe_key=dedupe_key,
            )
            if duplicate is not None:
                return None
        duplicate = await self.repository.find_recent_duplicate(
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            window_hours=dedupe_window_hours,
        )
        if duplicate is not None:
            return None
        row = await self.repository.create(
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type=notification_type,
            severity=severity,
            priority=priority,
            title=title,
            message=message,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=True, default=str),
            dedupe_key=dedupe_key,
            action_url=action_url,
            scheduled_for=scheduled_for,
            created_at=datetime.now(timezone.utc),
        )
        if get_settings().kafka_enabled:
            await OutboxService(self.session).add_notification_message(
                notification_id=int(row.id),
                tenant_id=tenant_id,
                user_id=user_id,
                notification_type=notification_type,
                idempotency_key=dedupe_key or f"notification:{tenant_id}:{user_id}:{row.id}",
            )
        if commit:
            await self.session.commit()
        payload = self._serialize(row)
        await realtime_hub.send_user(
            tenant_id,
            user_id,
            {
                "type": "notification.created",
                "notification": payload,
            },
        )
        return payload

    async def generate_due_notifications(self, *, tenant_id: int | None = None, limit_users: int = 100) -> int:
        learners_stmt = (
            select(User.id, User.tenant_id)
            .where(User.role == UserRole.student)
            .order_by(User.id.asc())
            .limit(limit_users)
        )
        if tenant_id is not None:
            learners_stmt = learners_stmt.where(User.tenant_id == tenant_id)
        learners = (await self.session.execute(learners_stmt)).all()
        created = 0
        for user_id, learner_tenant_id in learners:
            payloads = await self._candidate_notifications(tenant_id=int(learner_tenant_id), user_id=int(user_id))
            for payload in payloads:
                persisted = await self.create_notification(
                    tenant_id=int(learner_tenant_id),
                    user_id=int(user_id),
                    notification_type=payload["notification_type"],
                    severity=payload["severity"],
                    priority=payload.get("priority", "normal"),
                    title=payload["title"],
                    message=payload["message"],
                    metadata=payload.get("metadata"),
                    action_url=payload.get("action_url"),
                    dedupe_key=payload.get("dedupe_key"),
                    commit=False,
                )
                if persisted is not None:
                    created += 1
        await self.session.commit()
        return created

    async def _candidate_notifications(self, *, tenant_id: int, user_id: int) -> list[dict]:
        roadmap_steps = await self._roadmap_steps(tenant_id=tenant_id, user_id=user_id)
        topic_scores = await self._topic_scores(tenant_id=tenant_id, user_id=user_id)
        last_activity_at = await self._last_activity_at(tenant_id=tenant_id, user_id=user_id)
        notifications = self.mentor_notification_service.build_notifications(
            roadmap_steps=roadmap_steps,
            topic_scores=topic_scores,
            last_activity_at=last_activity_at,
        )
        return [
            {
                "notification_type": item.trigger,
                "severity": item.severity,
                "priority": "high" if item.severity in {"warning", "critical"} else "normal",
                "title": item.title,
                "message": item.message,
                "action_url": "/student/notifications",
                "metadata": {"source": "scheduled"},
                "dedupe_key": f"scheduled:{tenant_id}:{user_id}:{item.trigger}:{item.title.strip().lower()}",
            }
            for item in notifications
        ]

    async def _roadmap_steps(self, *, tenant_id: int, user_id: int) -> list[dict]:
        latest_roadmap_id = (
            await self.session.execute(
                select(Roadmap.id)
                .where(Roadmap.user_id == user_id)
                .order_by(Roadmap.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if latest_roadmap_id is None:
            return []
        rows = (
            await self.session.execute(
                select(RoadmapStep.topic_id, RoadmapStep.progress_status, RoadmapStep.deadline)
                .join(Roadmap, Roadmap.id == RoadmapStep.roadmap_id)
                .where(Roadmap.id == latest_roadmap_id, Roadmap.user_id == user_id)
            )
        ).all()
        return [
            {"topic_id": int(topic_id), "progress_status": progress_status, "deadline": deadline}
            for topic_id, progress_status, deadline in rows
        ]

    async def _topic_scores(self, *, tenant_id: int, user_id: int) -> dict[int, float]:
        rows = (
            await self.session.execute(
                select(TopicScore.topic_id, TopicScore.score).where(
                    TopicScore.tenant_id == tenant_id,
                    TopicScore.user_id == user_id,
                )
            )
        ).all()
        if rows:
            return {int(topic_id): float(score) for topic_id, score in rows}

        vectors = (
            await self.session.execute(
                select(UserSkillVector.topic_id, UserSkillVector.mastery_score).where(
                    UserSkillVector.tenant_id == tenant_id,
                    UserSkillVector.user_id == user_id,
                )
            )
        ).all()
        return {int(topic_id): float(mastery_score) for topic_id, mastery_score in vectors}

    async def _last_activity_at(self, *, tenant_id: int, user_id: int) -> datetime | None:
        return (
            await self.session.execute(
                select(func.max(func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at))).where(
                    LearningEvent.tenant_id == tenant_id,
                    LearningEvent.user_id == user_id,
                )
            )
        ).scalar_one_or_none()

    @staticmethod
    def _serialize(row: Notification) -> dict:
        return {
            "id": row.id,
            "notification_type": row.notification_type,
            "severity": row.severity,
            "priority": row.priority,
            "title": row.title,
            "message": row.message,
            "action_url": row.action_url,
            "created_at": row.created_at.isoformat(),
            "read_at": row.read_at.isoformat() if row.read_at is not None else None,
        }
