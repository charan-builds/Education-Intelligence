from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.application.services.diagnostic_service import DiagnosticService
from app.application.services.kafka_consumer_service import KafkaConsumerService
from app.application.services.ml_platform_service import MLPlatformService
from app.application.services.notification_service import NotificationService
from app.application.services.outbox_service import OutboxService
from app.application.services.precomputed_analytics_service import PrecomputedAnalyticsService
from app.application.services.roadmap_service import RoadmapService
from app.application.services.mentor_notification_service import MentorNotificationService
from app.application.services.skill_vector_service import SkillVectorService
from app.core.config import get_settings
from app.domain.models.learning_event import LearningEvent
from app.domain.models.notification import Notification
from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.jobs.celery_app import celery_app
from app.core.metrics import event_processing_duration_seconds

logger = logging.getLogger("learning_platform.jobs")


def _record_task_duration(task_name: str, status: str, started_at: float) -> None:
    event_processing_duration_seconds.labels(task_name=task_name, status=status).observe(max(time.perf_counter() - started_at, 0.0))


async def _run_generate_roadmap(user_id: int, tenant_id: int, goal_id: int, test_id: int) -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        roadmap = await RoadmapService(session).generate(
            user_id=user_id,
            tenant_id=tenant_id,
            goal_id=goal_id,
            test_id=test_id,
        )
        return {
            "roadmap_id": roadmap.id,
            "user_id": roadmap.user_id,
            "goal_id": roadmap.goal_id,
        }


@celery_app.task(name="jobs.generate_roadmap")
def generate_roadmap(user_id: int, tenant_id: int, goal_id: int, test_id: int) -> dict[str, Any]:
    started_at = time.perf_counter()
    try:
        result = asyncio.run(_run_generate_roadmap(user_id, tenant_id, goal_id, test_id))
        _record_task_duration("jobs.generate_roadmap", "success", started_at)
        logger.info(
            "generate_roadmap completed",
            extra={"user_id": user_id, "tenant_id": tenant_id, "goal_id": goal_id, "test_id": test_id},
        )
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.generate_roadmap", "failed", started_at)
        logger.exception(
            "generate_roadmap failed",
            extra={"user_id": user_id, "tenant_id": tenant_id, "goal_id": goal_id, "test_id": test_id},
        )
        raise exc


async def _run_analyze_diagnostic(test_id: int, user_id: int, tenant_id: int) -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        scores = await DiagnosticService(session).get_result(test_id=test_id, user_id=user_id, tenant_id=tenant_id)
        weak_topics = sorted([topic_id for topic_id, score in scores.items() if float(score) < 70.0])
        return {
            "test_id": test_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "topic_scores": scores,
            "weak_topics": weak_topics,
        }


@celery_app.task(name="jobs.analyze_diagnostic")
def analyze_diagnostic(test_id: int, user_id: int, tenant_id: int) -> dict[str, Any]:
    try:
        result = asyncio.run(_run_analyze_diagnostic(test_id, user_id, tenant_id))
        logger.info(
            "analyze_diagnostic completed",
            extra={"test_id": test_id, "user_id": user_id, "tenant_id": tenant_id},
        )
        return result
    except Exception as exc:  # pragma: no cover
        logger.exception(
            "analyze_diagnostic failed",
            extra={"test_id": test_id, "user_id": user_id, "tenant_id": tenant_id},
        )
        raise exc


async def _run_process_learning_event(event_id: int) -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        event = await session.get(LearningEvent, event_id)
        if event is None:
            return {"status": "missing", "event_id": event_id}
        await MLPlatformService(session).build_feature_snapshot(user_id=event.user_id, tenant_id=event.tenant_id)
        return {"status": "processed", "event_id": event_id, "user_id": event.user_id, "tenant_id": event.tenant_id}


@celery_app.task(name="jobs.process_learning_event", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_learning_event(event_id: int) -> dict[str, Any]:
    started_at = time.perf_counter()
    try:
        result = asyncio.run(_run_process_learning_event(event_id))
        _record_task_duration("jobs.process_learning_event", "success", started_at)
        logger.info("process_learning_event completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.process_learning_event", "failed", started_at)
        logger.exception("process_learning_event failed", extra={"event_id": event_id})
        raise exc


async def _run_send_notifications(
    roadmap_steps: list[dict[str, Any]],
    topic_scores: dict[int, float],
    last_activity_at_iso: str | None,
) -> list[dict[str, str]]:
    from datetime import datetime

    last_activity = datetime.fromisoformat(last_activity_at_iso) if last_activity_at_iso else None
    normalized_steps: list[dict[str, Any]] = []
    for step in roadmap_steps:
        normalized = dict(step)
        deadline = normalized.get("deadline")
        if isinstance(deadline, str):
            try:
                normalized["deadline"] = datetime.fromisoformat(deadline)
            except ValueError:
                normalized["deadline"] = None
        normalized_steps.append(normalized)
    service = MentorNotificationService()
    notifications = service.build_notifications(
        roadmap_steps=normalized_steps,
        topic_scores=topic_scores,
        last_activity_at=last_activity,
    )
    return [
        {
            "trigger": n.trigger,
            "severity": n.severity,
            "title": n.title,
            "message": n.message,
        }
        for n in notifications
    ]


@celery_app.task(name="jobs.send_notifications")
def send_notifications(
    roadmap_steps: list[dict[str, Any]],
    topic_scores: dict[int, float],
    last_activity_at_iso: str | None = None,
) -> list[dict[str, str]]:
    try:
        result = asyncio.run(_run_send_notifications(roadmap_steps, topic_scores, last_activity_at_iso))
        logger.info("send_notifications completed", extra={"count": len(result)})
        return result
    except Exception as exc:  # pragma: no cover
        logger.exception("send_notifications failed")
        raise exc


async def _run_generate_notifications(tenant_id: int | None = None, limit_users: int = 100) -> dict[str, int | None]:
    async with AsyncSessionLocal() as session:
        created = await NotificationService(session).generate_due_notifications(tenant_id=tenant_id, limit_users=limit_users)
        return {"created": created, "tenant_id": tenant_id}


@celery_app.task(name="jobs.generate_notifications", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def generate_notifications(tenant_id: int | None = None, limit_users: int = 100) -> dict[str, int | None]:
    started_at = time.perf_counter()
    try:
        result = asyncio.run(_run_generate_notifications(tenant_id=tenant_id, limit_users=limit_users))
        _record_task_duration("jobs.generate_notifications", "success", started_at)
        logger.info("generate_notifications completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.generate_notifications", "failed", started_at)
        logger.exception("generate_notifications failed", extra={"tenant_id": tenant_id, "limit_users": limit_users})
        raise exc


async def _run_decay_skill_vectors(tenant_id: int | None = None, inactive_days: int = 21) -> dict[str, int | None]:
    async with AsyncSessionLocal() as session:
        decayed = await SkillVectorService(session).decay_inactive_vectors(tenant_id=tenant_id, inactive_days=inactive_days)
        return {"decayed": decayed, "tenant_id": tenant_id}


@celery_app.task(name="jobs.decay_skill_vectors", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def decay_skill_vectors(tenant_id: int | None = None, inactive_days: int = 21) -> dict[str, int | None]:
    try:
        result = asyncio.run(_run_decay_skill_vectors(tenant_id=tenant_id, inactive_days=inactive_days))
        logger.info("decay_skill_vectors completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        logger.exception("decay_skill_vectors failed", extra={"tenant_id": tenant_id, "inactive_days": inactive_days})
        raise exc


async def _run_process_outbox_events(limit: int = 100) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        sent = await OutboxService(session).flush_pending_events(limit=limit)
        return {"dispatched": sent}


@celery_app.task(name="jobs.process_outbox_events")
def process_outbox_events(limit: int = 100) -> dict[str, int]:
    started_at = time.perf_counter()
    try:
        result = asyncio.run(_run_process_outbox_events(limit=limit))
        _record_task_duration("jobs.process_outbox_events", "success", started_at)
        logger.info("process_outbox_events completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.process_outbox_events", "failed", started_at)
        logger.exception("process_outbox_events failed", extra={"limit": limit})
        raise exc


async def _run_cleanup_outbox_events() -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        return await OutboxService(session).cleanup_old_events()


@celery_app.task(name="jobs.cleanup_outbox_events")
def cleanup_outbox_events() -> dict[str, int]:
    try:
        result = asyncio.run(_run_cleanup_outbox_events())
        logger.info("cleanup_outbox_events completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        logger.exception("cleanup_outbox_events failed")
        raise exc


async def _run_refresh_outbox_metrics() -> dict[str, str]:
    async with AsyncSessionLocal() as session:
        await OutboxService(session).refresh_queue_depth_metrics()
        return {"status": "ok"}


@celery_app.task(name="jobs.refresh_outbox_metrics")
def refresh_outbox_metrics() -> dict[str, str]:
    try:
        result = asyncio.run(_run_refresh_outbox_metrics())
        logger.info("refresh_outbox_metrics completed")
        return result
    except Exception as exc:  # pragma: no cover
        logger.exception("refresh_outbox_metrics failed")
        raise exc


async def _run_recover_stuck_outbox_events(limit: int = 500) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        recovered = await OutboxService(session).recover_stuck_processing_events(limit=limit)
        return {"recovered": recovered}


@celery_app.task(name="jobs.recover_stuck_outbox_events")
def recover_stuck_outbox_events(limit: int = 500) -> dict[str, int]:
    started_at = time.perf_counter()
    try:
        result = asyncio.run(_run_recover_stuck_outbox_events(limit=limit))
        _record_task_duration("jobs.recover_stuck_outbox_events", "success", started_at)
        logger.info("recover_stuck_outbox_events completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.recover_stuck_outbox_events", "failed", started_at)
        logger.exception("recover_stuck_outbox_events failed", extra={"limit": limit})
        raise exc


async def _run_refresh_precomputed_analytics(tenant_id: int | None = None, limit_users: int = 250) -> dict[str, int | None]:
    async with AsyncSessionLocal() as session:
        service = PrecomputedAnalyticsService(session)
        refreshed_tenants = 0
        if tenant_id is not None:
            await service.refresh_tenant_dashboard(tenant_id=tenant_id)
            refreshed_tenants = 1
        else:
            from sqlalchemy import select
            from app.domain.models.user import User, UserRole

            tenant_rows = (
                await session.execute(
                    select(User.tenant_id).where(User.role == UserRole.student).distinct().limit(limit_users)
                )
            ).all()
            for row in tenant_rows:
                await service.refresh_tenant_dashboard(tenant_id=int(row.tenant_id))
                refreshed_tenants += 1
        await session.commit()
        return {"refreshed_tenants": refreshed_tenants, "tenant_id": tenant_id}


@celery_app.task(name="jobs.refresh_precomputed_analytics", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def refresh_precomputed_analytics(tenant_id: int | None = None, limit_users: int = 250) -> dict[str, int | None]:
    started_at = time.perf_counter()
    try:
        result = asyncio.run(_run_refresh_precomputed_analytics(tenant_id=tenant_id, limit_users=limit_users))
        _record_task_duration("jobs.refresh_precomputed_analytics", "success", started_at)
        logger.info("refresh_precomputed_analytics completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.refresh_precomputed_analytics", "failed", started_at)
        logger.exception("refresh_precomputed_analytics failed", extra={"tenant_id": tenant_id})
        raise exc


async def _run_process_notification_event(notification_id: int) -> dict[str, int | str]:
    async with AsyncSessionLocal() as session:
        notification = await session.get(Notification, notification_id)
        if notification is None:
            return {"status": "missing", "notification_id": notification_id}
        return {"status": "processed", "notification_id": notification_id, "tenant_id": int(notification.tenant_id)}


@celery_app.task(name="jobs.process_notification_event", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_notification_event(notification_id: int) -> dict[str, int | str]:
    started_at = time.perf_counter()
    try:
        result = asyncio.run(_run_process_notification_event(notification_id))
        _record_task_duration("jobs.process_notification_event", "success", started_at)
        logger.info("process_notification_event completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.process_notification_event", "failed", started_at)
        logger.exception("process_notification_event failed", extra={"notification_id": notification_id})
        raise exc


async def _run_process_analytics_event(tenant_id: int, snapshot_type: str, subject_id: int | None = None) -> dict[str, int | str | None]:
    return {"status": "processed", "tenant_id": tenant_id, "snapshot_type": snapshot_type, "subject_id": subject_id}


@celery_app.task(name="jobs.process_analytics_event", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_analytics_event(tenant_id: int, snapshot_type: str, subject_id: int | None = None) -> dict[str, int | str | None]:
    started_at = time.perf_counter()
    try:
        result = asyncio.run(_run_process_analytics_event(tenant_id=tenant_id, snapshot_type=snapshot_type, subject_id=subject_id))
        _record_task_duration("jobs.process_analytics_event", "success", started_at)
        logger.info("process_analytics_event completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.process_analytics_event", "failed", started_at)
        logger.exception("process_analytics_event failed", extra={"tenant_id": tenant_id, "snapshot_type": snapshot_type})
        raise exc


async def _run_consume_kafka_events(limit: int = 100) -> dict[str, int]:
    if not get_settings().kafka_enabled:
        return {"processed": 0, "duplicate": 0, "failed": 0}
    async with AsyncSessionLocal() as session:
        service = KafkaConsumerService(session, consumer_group="learning-platform-celery")
        return await service.poll_and_process(max_records=limit)


@celery_app.task(name="jobs.consume_kafka_events", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def consume_kafka_events(limit: int = 100) -> dict[str, int]:
    started_at = time.perf_counter()
    try:
        result = asyncio.run(_run_consume_kafka_events(limit=limit))
        _record_task_duration("jobs.consume_kafka_events", "success", started_at)
        logger.info("consume_kafka_events completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.consume_kafka_events", "failed", started_at)
        logger.exception("consume_kafka_events failed", extra={"limit": limit})
        raise exc


async def _run_replay_kafka_topic(topic: str, partition: int, offset: int, limit: int = 100) -> dict[str, int]:
    if not get_settings().kafka_enabled:
        return {"processed": 0, "duplicate": 0, "failed": 0}
    async with AsyncSessionLocal() as session:
        service = KafkaConsumerService(session, consumer_group="learning-platform-replay")
        return await service.replay_from_offset(topic=topic, partition=partition, offset=offset, max_records=limit)


@celery_app.task(name="jobs.replay_kafka_topic", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def replay_kafka_topic(topic: str, partition: int, offset: int, limit: int = 100) -> dict[str, int]:
    started_at = time.perf_counter()
    try:
        result = asyncio.run(_run_replay_kafka_topic(topic=topic, partition=partition, offset=offset, limit=limit))
        _record_task_duration("jobs.replay_kafka_topic", "success", started_at)
        logger.info("replay_kafka_topic completed", extra={"topic": topic, "partition": partition, "offset": offset, **result})
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.replay_kafka_topic", "failed", started_at)
        logger.exception("replay_kafka_topic failed", extra={"topic": topic, "partition": partition, "offset": offset})
        raise exc
