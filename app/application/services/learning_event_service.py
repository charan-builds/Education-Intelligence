import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.outbox_service import OutboxService
from app.core.config import get_settings
from app.core.metrics import learning_events_total
from app.domain.models.learning_event import LearningEvent


class LearningEventService:
    EVENT_QUESTION_ANSWERED = "question_answered"
    EVENT_TOPIC_COMPLETED = "topic_completed"
    EVENT_DIAGNOSTIC_COMPLETED = "diagnostic_completed"
    EVENT_TOPIC_VIEWED = "topic_viewed"
    EVENT_ROADMAP_STEP_UPDATED = "roadmap_step_updated"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def track_event(
        self,
        tenant_id: int,
        user_id: int,
        event_type: str,
        action_type: str | None = None,
        topic_id: int | None = None,
        diagnostic_test_id: int | None = None,
        time_spent_seconds: int | None = None,
        metadata: dict | None = None,
        event_timestamp: datetime | None = None,
        schema_version: str = "v1",
        idempotency_key: str | None = None,
        commit: bool = True,
    ) -> LearningEvent:
        if idempotency_key:
            existing = await self.session.scalar(
                select(LearningEvent).where(
                    LearningEvent.tenant_id == tenant_id,
                    LearningEvent.user_id == user_id,
                    LearningEvent.idempotency_key == idempotency_key,
                )
            )
            if existing is not None:
                learning_events_total.labels(event_type=event_type, result="deduplicated").inc()
                return existing
        occurred_at = event_timestamp or datetime.now(timezone.utc)
        event = LearningEvent(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            action_type=action_type or event_type,
            topic_id=topic_id,
            diagnostic_test_id=diagnostic_test_id,
            time_spent_seconds=time_spent_seconds,
            metadata_json=json.dumps(metadata or {}, default=str),
            schema_version=schema_version,
            idempotency_key=idempotency_key,
            event_timestamp=occurred_at,
            created_at=occurred_at,
        )
        self.session.add(event)
        await self.session.flush()
        learning_events_total.labels(event_type=event_type, result="accepted").inc()
        if commit:
            outbox = OutboxService(self.session)
            if get_settings().kafka_enabled:
                effective_idempotency_key = idempotency_key or f"learning-event:{tenant_id}:{user_id}:{event.id}:{uuid4().hex}"
                await outbox.add_learning_event_message(
                    event_id=int(event.id),
                    tenant_id=tenant_id,
                    user_id=user_id,
                    event_type=event_type,
                    schema_version=schema_version,
                    idempotency_key=effective_idempotency_key,
                )
            else:
                await outbox.add_task_event(
                    task_name="jobs.process_learning_event",
                    args=[int(event.id)],
                    tenant_id=tenant_id,
                )
            await self.session.commit()
        return event

    async def track_question_answered(
        self,
        tenant_id: int,
        user_id: int,
        topic_id: int,
        diagnostic_test_id: int,
        question_id: int,
        score: float,
        time_taken: float,
        idempotency_key: str | None = None,
        commit: bool = True,
    ) -> LearningEvent:
        return await self.track_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=self.EVENT_QUESTION_ANSWERED,
            action_type="retry" if float(score) < 50.0 else "complete",
            topic_id=topic_id,
            diagnostic_test_id=diagnostic_test_id,
            time_spent_seconds=int(time_taken),
            metadata={
                "question_id": question_id,
                "score": score,
                "time_taken": time_taken,
            },
            idempotency_key=idempotency_key,
            commit=commit,
        )

    async def track_topic_completed(
        self,
        tenant_id: int,
        user_id: int,
        topic_id: int,
        completion_score: float,
        commit: bool = True,
    ) -> LearningEvent:
        return await self.track_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=self.EVENT_TOPIC_COMPLETED,
            action_type="complete",
            topic_id=topic_id,
            metadata={"completion_score": completion_score},
            commit=commit,
        )

    async def track_diagnostic_completed(
        self,
        tenant_id: int,
        user_id: int,
        diagnostic_test_id: int,
        goal_id: int,
        idempotency_key: str | None = None,
        commit: bool = True,
    ) -> LearningEvent:
        return await self.track_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=self.EVENT_DIAGNOSTIC_COMPLETED,
            action_type="complete",
            diagnostic_test_id=diagnostic_test_id,
            metadata={"goal_id": goal_id},
            idempotency_key=idempotency_key,
            commit=commit,
        )

    async def track_learning_action(
        self,
        *,
        tenant_id: int,
        user_id: int,
        action_type: str,
        topic_id: int | None = None,
        time_spent_seconds: int | None = None,
        metadata: dict | None = None,
        commit: bool = True,
    ) -> LearningEvent:
        return await self.track_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=f"learning_{action_type}",
            action_type=action_type,
            topic_id=topic_id,
            time_spent_seconds=time_spent_seconds,
            metadata=metadata,
            commit=commit,
        )
