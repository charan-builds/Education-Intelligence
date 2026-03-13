from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.application.services.diagnostic_service import DiagnosticService
from app.application.services.outbox_service import OutboxService
from app.application.services.roadmap_service import RoadmapService
from app.application.services.mentor_notification_service import MentorNotificationService
from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.jobs.celery_app import celery_app

logger = logging.getLogger("learning_platform.jobs")


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
    try:
        result = asyncio.run(_run_generate_roadmap(user_id, tenant_id, goal_id, test_id))
        logger.info(
            "generate_roadmap completed",
            extra={"user_id": user_id, "tenant_id": tenant_id, "goal_id": goal_id, "test_id": test_id},
        )
        return result
    except Exception as exc:  # pragma: no cover
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


async def _run_process_outbox_events(limit: int = 100) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        sent = await OutboxService(session).flush_pending_events(limit=limit)
        return {"dispatched": sent}


@celery_app.task(name="jobs.process_outbox_events")
def process_outbox_events(limit: int = 100) -> dict[str, int]:
    try:
        result = asyncio.run(_run_process_outbox_events(limit=limit))
        logger.info("process_outbox_events completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
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
    try:
        result = asyncio.run(_run_recover_stuck_outbox_events(limit=limit))
        logger.info("recover_stuck_outbox_events completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        logger.exception("recover_stuck_outbox_events failed", extra={"limit": limit})
        raise exc
