import json

import pytest

from app.application.services.kafka_consumer_service import KafkaConsumerService
from app.infrastructure.streaming.kafka_client import KafkaRecord


class _FakeConsumer:
    def __init__(self, records):
        self.records = records

    def poll(self, timeout_ms: int, max_records: int):
        return self.records[:max_records]

    def seek(self, topic: str, partition: int, offset: int):
        return None


class _FakeSession:
    async def commit(self):
        return None


@pytest.mark.asyncio
async def test_consumer_processes_learning_event_record(monkeypatch):
    dispatched = []
    seen = set()

    def _fake_enqueue(task_name, args=None, kwargs=None):
        dispatched.append((task_name, args, kwargs))
        return True

    async def _fake_has_processed(self, *, consumer_group, message_id):
        return message_id in seen

    async def _fake_record_processed_message(self, **kwargs):
        seen.add(kwargs["message_id"])
        return None

    async def _fake_upsert_offset(self, **kwargs):
        return None

    monkeypatch.setattr("app.application.services.kafka_consumer_service.enqueue_job", _fake_enqueue)
    monkeypatch.setattr("app.infrastructure.repositories.stream_offset_repository.StreamOffsetRepository.has_processed", _fake_has_processed)
    monkeypatch.setattr(
        "app.infrastructure.repositories.stream_offset_repository.StreamOffsetRepository.record_processed_message",
        _fake_record_processed_message,
    )
    monkeypatch.setattr("app.infrastructure.repositories.stream_offset_repository.StreamOffsetRepository.upsert_offset", _fake_upsert_offset)
    service = KafkaConsumerService(
        _FakeSession(),
        consumer_group="test-group",
        consumer=_FakeConsumer(
            [
                KafkaRecord(
                    topic="learning_events.v1",
                    partition=0,
                    offset=10,
                    key=b"1:2",
                    value=json.dumps(
                        {
                            "message_id": "message-1",
                            "topic": "learning_events",
                            "event_name": "learning_event.recorded",
                            "schema_version": "v1",
                            "partition_key": "1:2",
                            "idempotency_key": "abc",
                            "occurred_at": "2026-03-25T00:00:00+00:00",
                            "tenant_id": 1,
                            "user_id": 2,
                            "payload": {"event_id": 99, "event_type": "question_answered", "tenant_id": 1, "user_id": 2},
                        }
                    ).encode("utf-8"),
                )
            ]
        ),
    )

    result = await service.poll_and_process(max_records=10)

    assert result["processed"] == 1
    assert dispatched[0][0] == "jobs.process_learning_event"
