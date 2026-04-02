from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.events.schema_registry import validate_event_envelope
from app.infrastructure.jobs.dispatcher import enqueue_job
from app.infrastructure.repositories.stream_offset_repository import StreamOffsetRepository
from app.infrastructure.streaming.kafka_client import KafkaConsumerClient, KafkaRecord


class KafkaConsumerService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        consumer_group: str,
        consumer: KafkaConsumerClient | None = None,
    ):
        self.session = session
        self.consumer_group = consumer_group
        self.settings = get_settings()
        self.logger = get_logger()
        self.offset_repository = StreamOffsetRepository(session)
        self.consumer = consumer or KafkaConsumerClient(
            topics=[
                self.settings.kafka_topic_learning_events,
                self.settings.kafka_topic_notifications,
                self.settings.kafka_topic_analytics,
            ],
            group_id=consumer_group,
        )

    async def poll_and_process(self, *, max_records: int | None = None) -> dict[str, int]:
        processed = 0
        duplicate = 0
        failed = 0
        records = self.consumer.poll(
            timeout_ms=self.settings.kafka_consumer_poll_timeout_ms,
            max_records=max_records or self.settings.kafka_consumer_batch_size,
        )
        for record in records:
            try:
                was_duplicate = await self._process_record(record)
                processed += 0 if was_duplicate else 1
                duplicate += 1 if was_duplicate else 0
            except Exception:
                failed += 1
                self.logger.exception(
                    "failed to process kafka record",
                    extra={"log_data": {"topic": record.topic, "partition": record.partition, "offset": record.offset}},
                )
        await self.session.commit()
        return {"processed": processed, "duplicate": duplicate, "failed": failed}

    async def replay_from_offset(self, *, topic: str, partition: int, offset: int, max_records: int = 100) -> dict[str, int]:
        self.consumer.seek(topic, partition, offset)
        return await self.poll_and_process(max_records=max_records)

    async def _process_record(self, record: KafkaRecord) -> bool:
        payload = json.loads(record.value.decode("utf-8"))
        validate_event_envelope(payload)
        message_id = str(payload["message_id"])
        if await self.offset_repository.has_processed(consumer_group=self.consumer_group, message_id=message_id):
            await self.offset_repository.upsert_offset(
                consumer_group=self.consumer_group,
                topic=record.topic,
                partition=record.partition,
                offset=record.offset,
            )
            return True
        self._dispatch_to_celery(topic=record.topic, payload=payload)
        await self.offset_repository.record_processed_message(
            consumer_group=self.consumer_group,
            topic=record.topic,
            partition=record.partition,
            offset=record.offset,
            message_id=message_id,
            event_name=str(payload["event_name"]),
            tenant_id=payload.get("tenant_id"),
        )
        await self.offset_repository.upsert_offset(
            consumer_group=self.consumer_group,
            topic=record.topic,
            partition=record.partition,
            offset=record.offset,
        )
        return False

    def _dispatch_to_celery(self, *, topic: str, payload: dict) -> None:
        if topic == self.settings.kafka_topic_learning_events:
            enqueue_job("jobs.process_learning_event", args=[int(payload["payload"]["event_id"])])
            return
        if topic == self.settings.kafka_topic_notifications:
            enqueue_job(
                "jobs.process_notification_event",
                kwargs={"notification_id": int(payload["payload"]["notification_id"])},
            )
            return
        if topic == self.settings.kafka_topic_analytics:
            enqueue_job(
                "jobs.process_analytics_event",
                kwargs={
                    "tenant_id": int(payload["payload"]["tenant_id"]),
                    "snapshot_type": str(payload["payload"]["snapshot_type"]),
                    "subject_id": payload["payload"].get("subject_id"),
                },
            )
            return
        raise ValueError(f"Unsupported topic: {topic}")
