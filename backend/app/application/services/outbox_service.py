from __future__ import annotations

import json
import contextlib
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import (
    event_processing_duration_seconds,
    outbox_cleanup_removed_total,
    outbox_dead_total,
    outbox_dispatched_total,
    outbox_failed_total,
    outbox_processed_total,
    outbox_queue_depth,
    outbox_recovered_total,
)
from app.events.event_envelope import EventEnvelope
from app.events.kafka_topics import ANALYTICS_TOPIC, LEARNING_EVENTS_TOPIC, NOTIFICATIONS_TOPIC
from app.infrastructure.repositories.dead_letter_repository import DeadLetterRepository
from app.infrastructure.repositories.outbox_repository import OutboxRepository


class OutboxService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = OutboxRepository(session)
        self.dead_letter_repository = DeadLetterRepository(session)
        self.settings = get_settings()
        self.logger = get_logger()

    async def add_task_event(
        self,
        *,
        task_name: str,
        args: list | None = None,
        kwargs: dict | None = None,
        tenant_id: int | None = None,
        idempotency_key: str | None = None,
    ) -> int:
        payload = {
            "task_name": task_name,
            "args": list(args or []),
            "kwargs": dict(kwargs or {}),
        }
        row = await self.repository.create_event(
            tenant_id=tenant_id,
            event_type="celery_task",
            payload_json=json.dumps(payload, separators=(",", ":"), sort_keys=True),
            idempotency_key=idempotency_key,
        )
        await self.refresh_queue_depth_metrics()
        return int(row.id)

    async def add_kafka_event(self, *, envelope: EventEnvelope) -> int:
        row = await self.repository.create_event(
            tenant_id=envelope.tenant_id,
            event_type="kafka_message",
            payload_json=json.dumps(envelope.to_dict(), separators=(",", ":"), sort_keys=True),
            idempotency_key=envelope.idempotency_key,
        )
        await self.refresh_queue_depth_metrics()
        return int(row.id)

    async def add_learning_event_message(
        self,
        *,
        event_id: int,
        tenant_id: int,
        user_id: int,
        event_type: str,
        schema_version: str,
        idempotency_key: str,
    ) -> int:
        return await self.add_kafka_event(
            envelope=EventEnvelope(
                topic=LEARNING_EVENTS_TOPIC,
                event_name="learning_event.recorded",
                schema_version=schema_version,
                tenant_id=tenant_id,
                user_id=user_id,
                partition_key=f"{tenant_id}:{user_id}",
                idempotency_key=idempotency_key,
                payload={
                    "event_id": event_id,
                    "event_type": event_type,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                },
            )
        )

    async def add_domain_event_message(
        self,
        *,
        event_name: str,
        tenant_id: int,
        user_id: int,
        payload: dict,
        schema_version: str = "v1",
        partition_key: str | None = None,
        idempotency_key: str,
    ) -> int:
        enriched_payload = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            **payload,
        }
        return await self.add_kafka_event(
            envelope=EventEnvelope(
                topic=LEARNING_EVENTS_TOPIC,
                event_name=event_name,
                schema_version=schema_version,
                tenant_id=tenant_id,
                user_id=user_id,
                partition_key=partition_key or f"{tenant_id}:{user_id}",
                idempotency_key=idempotency_key,
                payload=enriched_payload,
            )
        )

    async def add_notification_message(
        self,
        *,
        notification_id: int,
        tenant_id: int,
        user_id: int,
        notification_type: str,
        idempotency_key: str,
    ) -> int:
        return await self.add_kafka_event(
            envelope=EventEnvelope(
                topic=NOTIFICATIONS_TOPIC,
                event_name="notification.created",
                schema_version="v1",
                tenant_id=tenant_id,
                user_id=user_id,
                partition_key=f"{tenant_id}:{user_id}",
                idempotency_key=idempotency_key,
                payload={
                    "notification_id": notification_id,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "notification_type": notification_type,
                },
            )
        )

    async def add_analytics_message(
        self,
        *,
        tenant_id: int,
        snapshot_type: str,
        window_start: str,
        window_end: str,
        subject_id: int | None = None,
        idempotency_key: str,
    ) -> int:
        return await self.add_kafka_event(
            envelope=EventEnvelope(
                topic=ANALYTICS_TOPIC,
                event_name="analytics.snapshot_refreshed",
                schema_version="v1",
                tenant_id=tenant_id,
                user_id=subject_id,
                partition_key=f"{tenant_id}:{snapshot_type}:{subject_id or 'tenant'}",
                idempotency_key=idempotency_key,
                payload={
                    "tenant_id": tenant_id,
                    "snapshot_type": snapshot_type,
                    "subject_id": subject_id,
                    "window_start": window_start,
                    "window_end": window_end,
                },
            )
        )

    async def flush_pending_events(self, *, limit: int = 100) -> int:
        import json

        from app.application.services.kafka_producer_service import KafkaProducerService
        from app.infrastructure.jobs.celery_app import celery_app

        events = await self.repository.list_ready(limit=limit)
        sent = 0
        kafka_producer: KafkaProducerService | None = None
        for event in events:
            started_at = datetime.now(timezone.utc)
            try:
                payload = json.loads(event.payload_json)
                if event.event_type == "kafka_message":
                    envelope = EventEnvelope(**payload)
                    if self.settings.kafka_enabled:
                        kafka_producer = kafka_producer or KafkaProducerService()
                        kafka_producer.publish(envelope)
                        task_name = f"kafka:{envelope.event_name}"
                    else:
                        if envelope.event_name == "learning_event.recorded":
                            celery_app.send_task(
                                "jobs.process_learning_event",
                                kwargs={
                                    "event_id": int(envelope.payload["event_id"]),
                                    "tenant_id": int(envelope.payload["tenant_id"]),
                                    "outbox_idempotency_key": envelope.idempotency_key,
                                },
                            )
                            task_name = "jobs.process_learning_event"
                        else:
                            celery_app.send_task(
                                "jobs.process_domain_event",
                                kwargs={
                                    "envelope": payload,
                                    "delivery_attempt": 1,
                                    "outbox_idempotency_key": envelope.idempotency_key,
                                },
                            )
                            task_name = f"jobs.process_domain_event:{envelope.event_name}"
                else:
                    task_name = str(payload.get("task_name"))
                    args = payload.get("args", [])
                    kwargs = payload.get("kwargs", {})
                    celery_app.send_task(task_name, args=args, kwargs=kwargs)
                await self.repository.mark_dispatched(event)
                outbox_dispatched_total.inc()
                event_processing_duration_seconds.labels(task_name=task_name, status="dispatched").observe(
                    max((datetime.now(timezone.utc) - started_at).total_seconds(), 0.0)
                )
                sent += 1
            except Exception as exc:
                await self.repository.mark_dispatch_failed(
                    event,
                    str(exc),
                    retry_delay_seconds=self.settings.outbox_retry_base_delay_seconds,
                    max_attempts=self.settings.outbox_max_attempts,
                )
                outbox_failed_total.inc()
                task_name = "unknown"
                with contextlib.suppress(Exception):
                    task_name = str(json.loads(event.payload_json).get("task_name", "unknown"))
                event_processing_duration_seconds.labels(task_name=task_name, status="failed").observe(
                    max((datetime.now(timezone.utc) - started_at).total_seconds(), 0.0)
                )
                if event.status == "dead":
                    await self.dead_letter_repository.create_event(
                        tenant_id=event.tenant_id,
                        source_event_id=int(event.id),
                        source_type="outbox",
                        event_type=event.event_type,
                        payload_json=event.payload_json,
                        error_message=str(exc),
                        attempts=int(event.attempts),
                    )
                    outbox_dead_total.inc()
                    self.logger.error(
                        "outbox event moved to dead letter queue",
                        extra={
                            "log_data": {
                                "outbox_event_id": int(event.id),
                                "tenant_id": event.tenant_id,
                                "attempts": int(event.attempts),
                                "error_message": str(exc)[:512],
                            }
                        },
                    )
        await self.session.commit()
        await self.refresh_queue_depth_metrics()
        return sent

    async def cleanup_old_events(self) -> dict[str, int]:
        removed_processed = await self.repository.delete_processed_older_than(self.settings.outbox_cleanup_days)
        removed_dead = await self.repository.delete_dead_older_than(self.settings.outbox_cleanup_days)
        removed_dlq = await self.dead_letter_repository.delete_older_than(days=self.settings.outbox_dead_letter_retention_days)
        await self.session.commit()
        if removed_processed:
            outbox_cleanup_removed_total.labels(status="processed").inc(removed_processed)
        if removed_dead:
            outbox_cleanup_removed_total.labels(status="dead").inc(removed_dead)
        await self.refresh_queue_depth_metrics()
        return {"removed_processed": removed_processed, "removed_dead": removed_dead, "removed_dlq": removed_dlq}

    async def list_events(
        self,
        *,
        status: str,
        tenant_id: int | None,
        limit: int,
        offset: int,
    ):
        return await self.repository.list_by_status(
            status=status,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )

    async def requeue_dead_events(self, *, tenant_id: int | None, limit: int) -> int:
        count = await self.repository.requeue_dead_events(tenant_id=tenant_id, limit=limit)
        await self.session.commit()
        await self.refresh_queue_depth_metrics()
        return count

    async def get_stats(self, *, tenant_id: int | None) -> dict[str, int]:
        queued = await self.repository.count_by_status(status="queued", tenant_id=tenant_id)
        failed = await self.repository.count_by_status(status="failed", tenant_id=tenant_id)
        dead = await self.repository.count_by_status(status="dead", tenant_id=tenant_id)
        dispatched = await self.repository.count_by_status(status="dispatched", tenant_id=tenant_id)
        processed = await self.repository.count_by_status(status="processed", tenant_id=tenant_id)
        return {
            "queued": queued,
            "dispatched": dispatched,
            "processed": processed,
            "failed": failed,
            "dead": dead,
            "pending": queued,
            "processing": dispatched,
        }

    async def requeue_dead_event_by_id(self, *, event_id: int, tenant_id: int | None) -> bool:
        updated = await self.repository.requeue_dead_event_by_id(event_id=event_id, tenant_id=tenant_id)
        await self.session.commit()
        if updated:
            await self.refresh_queue_depth_metrics()
        return updated

    async def recover_stuck_processing_events(self, *, limit: int = 500) -> int:
        recovered = await self.repository.recover_stuck_processing_events(
            timeout_seconds=self.settings.outbox_processing_timeout_seconds,
            limit=limit,
        )
        await self.session.commit()
        if recovered:
            outbox_recovered_total.inc(recovered)
        await self.refresh_queue_depth_metrics()
        return recovered

    async def refresh_queue_depth_metrics(self, tenant_id: int | None = None) -> None:
        queued = await self.repository.count_by_status(status="queued", tenant_id=tenant_id)
        failed = await self.repository.count_by_status(status="failed", tenant_id=tenant_id)
        dead = await self.repository.count_by_status(status="dead", tenant_id=tenant_id)
        dispatched = await self.repository.count_by_status(status="dispatched", tenant_id=tenant_id)
        processed = await self.repository.count_by_status(status="processed", tenant_id=tenant_id)
        outbox_queue_depth.labels(status="queued").set(float(queued))
        outbox_queue_depth.labels(status="dead").set(float(dead))
        outbox_queue_depth.labels(status="dispatched").set(float(dispatched))
        outbox_queue_depth.labels(status="processed").set(float(processed))
        outbox_queue_depth.labels(status="failed").set(float(failed))

    async def mark_kafka_message_processed(self, *, tenant_id: int | None, idempotency_key: str) -> bool:
        updated = await self.repository.mark_processed_by_idempotency_key(
            tenant_id=tenant_id,
            event_type="kafka_message",
            idempotency_key=idempotency_key,
        )
        if updated:
            outbox_processed_total.inc()
            await self.session.commit()
        return updated

    async def mark_kafka_message_failed(self, *, tenant_id: int | None, idempotency_key: str, error_message: str, dead: bool = False) -> bool:
        updated = await self.repository.mark_consumption_failed_by_idempotency_key(
            tenant_id=tenant_id,
            event_type="kafka_message",
            idempotency_key=idempotency_key,
            error_message=error_message,
            dead=dead,
        )
        if updated:
            if dead:
                outbox_dead_total.inc()
            else:
                outbox_failed_total.inc()
            await self.session.commit()
        return updated
