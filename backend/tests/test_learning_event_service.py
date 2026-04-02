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


def test_track_question_answered_event_payload(monkeypatch):
    async def _run():
        async def _noop(*args, **kwargs):
            return 1

        monkeypatch.setattr("app.application.services.outbox_service.OutboxService.add_task_event", _noop)
        monkeypatch.setattr("app.application.services.outbox_service.OutboxService.add_learning_event_message", _noop)
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


def test_track_question_answered_is_idempotent(monkeypatch):
    async def _run():
        async def _noop(*args, **kwargs):
            return 1

        monkeypatch.setattr("app.application.services.outbox_service.OutboxService.add_task_event", _noop)
        monkeypatch.setattr("app.application.services.outbox_service.OutboxService.add_learning_event_message", _noop)

        class _IdempotentSession(_Session):
            async def scalar(self, stmt):
                tenant_id = list(stmt._where_criteria)[0].right.value
                user_id = list(stmt._where_criteria)[1].right.value
                idem_key = list(stmt._where_criteria)[2].right.value
                for event in self.events:
                    if (
                        event.tenant_id == tenant_id
                        and event.user_id == user_id
                        and event.idempotency_key == idem_key
                    ):
                        return event
                return None

        session = _IdempotentSession()
        service = LearningEventService(session)

        first = await service.track_question_answered(
            tenant_id=1,
            user_id=2,
            topic_id=10,
            diagnostic_test_id=5,
            question_id=100,
            score=85.0,
            time_taken=12.5,
            idempotency_key="diagnostic-answer:1:2:5:100",
        )
        second = await service.track_question_answered(
            tenant_id=1,
            user_id=2,
            topic_id=10,
            diagnostic_test_id=5,
            question_id=100,
            score=85.0,
            time_taken=12.5,
            idempotency_key="diagnostic-answer:1:2:5:100",
        )

        assert first is second
        assert len(session.events) == 1

    asyncio.run(_run())
