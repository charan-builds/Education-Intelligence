from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.metrics import (
    outbox_cleanup_removed_total,
    outbox_dead_total,
    outbox_dispatched_total,
    outbox_failed_total,
    outbox_queue_depth,
    outbox_recovered_total,
)
from app.infrastructure.repositories.outbox_repository import OutboxRepository


class OutboxService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = OutboxRepository(session)
        self.settings = get_settings()

    async def add_task_event(
        self,
        *,
        task_name: str,
        args: list | None = None,
        kwargs: dict | None = None,
        tenant_id: int | None = None,
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
        )
        await self.refresh_queue_depth_metrics()
        return int(row.id)

    async def flush_pending_events(self, *, limit: int = 100) -> int:
        import json

        from app.infrastructure.jobs.celery_app import celery_app

        events = await self.repository.list_pending(limit=limit)
        sent = 0
        for event in events:
            try:
                await self.repository.mark_processing(event)
                payload = json.loads(event.payload_json)
                task_name = str(payload.get("task_name"))
                args = payload.get("args", [])
                kwargs = payload.get("kwargs", {})
                celery_app.send_task(task_name, args=args, kwargs=kwargs)
                await self.repository.mark_dispatched(event)
                outbox_dispatched_total.inc()
                sent += 1
            except Exception as exc:
                await self.repository.mark_failed(
                    event,
                    str(exc),
                    retry_delay_seconds=self.settings.outbox_retry_delay_seconds,
                    max_attempts=self.settings.outbox_max_attempts,
                )
                outbox_failed_total.inc()
                if event.status == "dead":
                    outbox_dead_total.inc()
        await self.session.commit()
        await self.refresh_queue_depth_metrics()
        return sent

    async def cleanup_old_events(self) -> dict[str, int]:
        removed_dispatched = await self.repository.delete_dispatched_older_than(self.settings.outbox_cleanup_days)
        removed_dead = await self.repository.delete_dead_older_than(self.settings.outbox_cleanup_days)
        await self.session.commit()
        if removed_dispatched:
            outbox_cleanup_removed_total.labels(status="dispatched").inc(removed_dispatched)
        if removed_dead:
            outbox_cleanup_removed_total.labels(status="dead").inc(removed_dead)
        await self.refresh_queue_depth_metrics()
        return {"removed_dispatched": removed_dispatched, "removed_dead": removed_dead}

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
        pending = await self.repository.count_by_status(status="pending", tenant_id=tenant_id)
        processing = await self.repository.count_by_status(status="processing", tenant_id=tenant_id)
        dead = await self.repository.count_by_status(status="dead", tenant_id=tenant_id)
        dispatched = await self.repository.count_by_status(status="dispatched", tenant_id=tenant_id)
        return {"pending": pending, "processing": processing, "dead": dead, "dispatched": dispatched}

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
        pending = await self.repository.count_by_status(status="pending", tenant_id=tenant_id)
        processing = await self.repository.count_by_status(status="processing", tenant_id=tenant_id)
        dead = await self.repository.count_by_status(status="dead", tenant_id=tenant_id)
        dispatched = await self.repository.count_by_status(status="dispatched", tenant_id=tenant_id)
        outbox_queue_depth.labels(status="pending").set(float(pending))
        outbox_queue_depth.labels(status="processing").set(float(processing))
        outbox_queue_depth.labels(status="dead").set(float(dead))
        outbox_queue_depth.labels(status="dispatched").set(float(dispatched))
