import json
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.learning_event import LearningEvent


class LearningEventService:
    EVENT_QUESTION_ANSWERED = "question_answered"
    EVENT_TOPIC_COMPLETED = "topic_completed"
    EVENT_DIAGNOSTIC_COMPLETED = "diagnostic_completed"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def track_event(
        self,
        tenant_id: int,
        user_id: int,
        event_type: str,
        topic_id: int | None = None,
        diagnostic_test_id: int | None = None,
        metadata: dict | None = None,
    ) -> LearningEvent:
        event = LearningEvent(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            topic_id=topic_id,
            diagnostic_test_id=diagnostic_test_id,
            metadata_json=json.dumps(metadata or {}, default=str),
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(event)
        await self.session.flush()
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
    ) -> LearningEvent:
        return await self.track_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=self.EVENT_QUESTION_ANSWERED,
            topic_id=topic_id,
            diagnostic_test_id=diagnostic_test_id,
            metadata={
                "question_id": question_id,
                "score": score,
                "time_taken": time_taken,
            },
        )

    async def track_topic_completed(
        self,
        tenant_id: int,
        user_id: int,
        topic_id: int,
        completion_score: float,
    ) -> LearningEvent:
        return await self.track_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=self.EVENT_TOPIC_COMPLETED,
            topic_id=topic_id,
            metadata={"completion_score": completion_score},
        )

    async def track_diagnostic_completed(
        self,
        tenant_id: int,
        user_id: int,
        diagnostic_test_id: int,
        goal_id: int,
    ) -> LearningEvent:
        return await self.track_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=self.EVENT_DIAGNOSTIC_COMPLETED,
            diagnostic_test_id=diagnostic_test_id,
            metadata={"goal_id": goal_id},
        )
