import asyncio
import json

from app.application.services.learning_event_service import LearningEventService


class _Session:
    def __init__(self):
        self.events = []

    def add(self, event):
        event.id = len(self.events) + 1
        self.events.append(event)

    async def flush(self):
        return None

    async def commit(self):
        return None


def test_track_question_answered_event_payload():
    async def _run():
        session = _Session()
        service = LearningEventService(session)

        event = await service.track_question_answered(
            tenant_id=1,
            user_id=2,
            topic_id=10,
            diagnostic_test_id=5,
            question_id=100,
            score=85.0,
            time_taken=12.5,
        )

        assert event.event_type == "question_answered"
        payload = json.loads(event.metadata_json)
        assert payload["question_id"] == 100
        assert payload["score"] == 85.0

    asyncio.run(_run())
