from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.notification_service import NotificationService
from app.application.services.precomputed_analytics_service import PrecomputedAnalyticsService
from app.application.services.skill_vector_service import SkillVectorService
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.jobs.dispatcher import enqueue_job_with_options
from app.domain.models.question import Question
from app.domain.models.topic import Topic
from app.domain.models.user_answer import UserAnswer
from app.events.schema_registry import validate_event_envelope
from app.infrastructure.repositories.event_consumer_state_repository import EventConsumerStateRepository


class DomainEventConsumerService:
    CONSUMER_NAME = "domain_event_consumer"

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = EventConsumerStateRepository(session)
        self.analytics_service = PrecomputedAnalyticsService(session)
        self.skill_vector_service = SkillVectorService(session)
        self.notification_service = NotificationService(session)
        self.cache = CacheService()
        self._handlers: dict[str, Callable[[dict], object]] = {
            "diagnostic_completed": self._handle_diagnostic_completed,
            "roadmap_generated": self._handle_roadmap_generated,
            "user_progress_updated": self._handle_user_progress_updated,
        }

    async def begin_processing(self, *, envelope: dict, attempt: int):
        validate_event_envelope(envelope)
        row = await self.repository.get_or_create(
            consumer_name=self.CONSUMER_NAME,
            event_name=str(envelope["event_name"]),
            message_id=str(envelope["message_id"]),
            tenant_id=envelope.get("tenant_id"),
        )
        if row.status == "processed":
            return row, True
        await self.repository.mark_processing(row, attempts=attempt)
        return row, False

    async def handle_event(self, *, envelope: dict) -> dict:
        event_name = str(envelope["event_name"])
        handler = self._handlers.get(event_name)
        if handler is None:
            raise ValueError(f"Unsupported domain event: {event_name}")
        result = await handler(envelope["payload"])
        return {"consumer": self.CONSUMER_NAME, "event_name": event_name, **result}

    async def mark_success(self, row, *, attempt: int) -> None:
        await self.repository.mark_processed(row, attempts=attempt)

    async def mark_failure(self, row, *, attempt: int, error_message: str, dead: bool) -> None:
        await self.repository.mark_failed(row, attempts=attempt, error_message=error_message, dead=dead)

    async def _schedule_coalesced_projection_refresh(
        self,
        *,
        projection_type: str,
        tenant_id: int,
        user_id: int,
        countdown: int = 5,
    ) -> bool:
        cache_key = self.cache.build_key(
            "event-projection-batch",
            projection_type=projection_type,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        if await self.cache.get(cache_key):
            return False
        await self.cache.set(cache_key, {"queued": True}, ttl=max(countdown + 10, 15))
        return enqueue_job_with_options(
            "jobs.refresh_user_projection",
            kwargs={"tenant_id": tenant_id, "user_id": user_id, "projection_type": projection_type},
            countdown=countdown,
        )

    async def _handle_diagnostic_completed(self, payload: dict) -> dict:
        tenant_id = int(payload["tenant_id"])
        user_id = int(payload["user_id"])
        snapshot = await self.analytics_service.refresh_user_diagnostic_summary(tenant_id=tenant_id, user_id=user_id)
        await self.analytics_service.refresh_student_performance_analytics(tenant_id=tenant_id, user_id=user_id)
        topic_rows = (
            await self.session.execute(
                select(Topic.id, Topic.name)
                .join(Question, Question.topic_id == Topic.id)
                .join(UserAnswer, UserAnswer.question_id == Question.id)
                .where(UserAnswer.test_id == int(payload["diagnostic_test_id"]), Topic.tenant_id == tenant_id)
                .distinct()
            )
        ).all()
        for topic_id, topic_name in topic_rows:
            await self.analytics_service.refresh_topic_performance_analytics(
                tenant_id=tenant_id,
                topic_id=int(topic_id),
                topic_name=str(topic_name),
            )
        await self.notification_service.create_notification(
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type="diagnostic_completed",
            severity="info",
            title="Diagnostic complete",
            message="Your diagnostic has been processed and your latest recommendations are ready.",
            action_url="/student/diagnostic",
            dedupe_key=f"consumer:diagnostic-completed:{tenant_id}:{user_id}:{int(payload['diagnostic_test_id'])}",
            commit=False,
        )
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "diagnostic_test_id": int(payload["diagnostic_test_id"]),
            "projection": "user_diagnostic_summary",
            "average_score": snapshot["average_score"],
        }

    async def _handle_roadmap_generated(self, payload: dict) -> dict:
        tenant_id = int(payload["tenant_id"])
        user_id = int(payload["user_id"])
        snapshot = await self.analytics_service.refresh_user_roadmap_stats(tenant_id=tenant_id, user_id=user_id)
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "roadmap_id": int(payload["roadmap_id"]),
            "projection": "user_roadmap_stats",
            "completion_percent": snapshot["completion_percent"],
        }

    async def _handle_user_progress_updated(self, payload: dict) -> dict:
        tenant_id = int(payload["tenant_id"])
        user_id = int(payload["user_id"])
        topic_id = int(payload["topic_id"])
        progress_status = str(payload["progress_status"])
        vector = await self.skill_vector_service.update_from_progress(
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
            progress_status=progress_status,
        )
        queued = await self._schedule_coalesced_projection_refresh(
            projection_type="user_roadmap_stats",
            tenant_id=tenant_id,
            user_id=user_id,
        )
        if progress_status in {"completed", "done"}:
            await self.notification_service.create_notification(
                tenant_id=tenant_id,
                user_id=user_id,
                notification_type="roadmap_step_completed",
                severity="success",
                title="Progress saved",
                message="A roadmap step was marked complete. Your progress summary has been updated.",
                action_url="/student/roadmap",
                dedupe_key=f"consumer:progress-updated:{tenant_id}:{user_id}:{int(payload['step_id'])}:{progress_status}",
                commit=False,
            )
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "step_id": int(payload["step_id"]),
            "topic_id": topic_id,
            "progress_status": progress_status,
            "projection": "skill_vector",
            "mastery_score": vector["mastery_score"],
            "batched_follow_up": queued,
        }
