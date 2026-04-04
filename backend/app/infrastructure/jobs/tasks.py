from __future__ import annotations

import asyncio
import functools
import logging
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select

from app.application.services.analytics_service import AnalyticsService
from app.application.services.analytics_snapshot_service import AnalyticsSnapshotService
from app.application.services.analytics_snapshot_types import (
    INSTITUTION_DASHBOARD_SNAPSHOT,
    PLATFORM_OVERVIEW_SNAPSHOT,
    SYSTEM_SUMMARY_SNAPSHOT,
    TEACHER_DASHBOARD_SNAPSHOT,
    TENANT_DASHBOARD_SNAPSHOT,
    USER_DASHBOARD_SNAPSHOT,
    USER_LEARNING_SUMMARY_SNAPSHOT,
    normalize_snapshot_type,
)
from app.application.services.diagnostic_service import DiagnosticService
from app.application.services.ai_request_service import AIRequestService
from app.application.services.domain_event_consumer_service import DomainEventConsumerService
from app.application.services.email_service import EmailPayload, EmailService
from app.application.services.kafka_consumer_service import KafkaConsumerService
from app.application.services.ml_platform_service import MLPlatformService
from app.application.services.mentor_service import MentorService
from app.application.services.notification_service import NotificationService
from app.application.services.outbox_service import OutboxService
from app.application.services.precomputed_analytics_service import PrecomputedAnalyticsService
from app.application.services.retention_service import RetentionService
from app.application.services.roadmap_service import RoadmapService
from app.application.services.mentor_notification_service import MentorNotificationService
from app.application.services.skill_vector_service import SkillVectorService
from app.core.config import get_settings
from app.core.metrics import (
    analytics_rebuild_dead_total,
    analytics_rebuild_jobs_total,
    analytics_rebuild_retries_total,
    domain_event_consumer_total,
    domain_event_retry_total,
)
from app.domain.models.learning_event import LearningEvent
from app.domain.models.notification import Notification
from app.domain.models.topic import Topic
from app.domain.models.user import UserRole
from app.domain.models.user_tenant_role import UserTenantRole
from app.infrastructure.repositories.mentor_chat_repository import MentorChatRepository
from app.infrastructure.repositories.dead_letter_repository import DeadLetterRepository
from app.infrastructure.database import open_super_admin_session, open_tenant_session
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.jobs.celery_app import celery_app
from app.infrastructure.jobs.queue_config import AI_QUEUE, ANALYTICS_QUEUE, CRITICAL_QUEUE, OPS_QUEUE
from app.core.metrics import event_processing_duration_seconds
from app.infrastructure.jobs.dispatcher import enqueue_job_with_options
from app.realtime.hub import realtime_hub

logger = logging.getLogger("learning_platform.jobs")
MAX_ANALYTICS_JOBS_PER_TENANT = 3


def enforce_queue(task_func):
    if not getattr(task_func, "queue", None):
        raise ValueError(f"Task {task_func.__name__} missing queue assignment")
    return task_func


def _print_task_queue_duration(task_self, start: float) -> None:
    request = getattr(task_self, "request", None)
    delivery_info = getattr(request, "delivery_info", None) if request is not None else None
    if not isinstance(delivery_info, dict):
        delivery_info = {}
    routing_key = delivery_info.get("routing_key", "unknown")
    duration = time.time() - start
    print(f"[QUEUE={routing_key}] duration={duration}")


def _task(*, queue: str, **kwargs):
    if not queue:
        raise ValueError("Celery tasks must declare an explicit queue")

    def _decorator(func):
        func.queue = queue
        enforce_queue(func)

        @functools.wraps(func)
        def _wrapped(*args, **inner_kwargs):
            task_self = args[0] if args else inner_kwargs.get("self")
            start = time.time()
            try:
                return func(*args, **inner_kwargs)
            finally:
                _print_task_queue_duration(task_self, start)

        _wrapped.queue = queue
        return celery_app.task(queue=queue, **kwargs)(_wrapped)

    return _decorator


def _run_async(coro):
    # Celery tasks enter here from synchronous worker code, so a fresh event loop
    # per invocation avoids cross-task loop state leaking between jobs.
    return asyncio.run(coro)


def _record_task_duration(task_name: str, status: str, started_at: float) -> None:
    event_processing_duration_seconds.labels(task_name=task_name, status=status).observe(max(time.perf_counter() - started_at, 0.0))


async def _run_global_super_admin_job(*, reason: str, operation):
    async with open_super_admin_session(reason=reason) as session:
        return await operation(session)


async def _mark_outbox_processed(*, tenant_id: int | None, idempotency_key: str | None) -> None:
    if not idempotency_key:
        return
    session_factory = (
        open_tenant_session(tenant_id=tenant_id, role="system")
        if tenant_id is not None
        else open_super_admin_session(reason="mark_outbox_processed_without_tenant")
    )
    async with session_factory as session:
        await OutboxService(session).mark_kafka_message_processed(tenant_id=tenant_id, idempotency_key=idempotency_key)


async def _mark_outbox_failed(*, tenant_id: int | None, idempotency_key: str | None, error_message: str, dead: bool = False) -> None:
    if not idempotency_key:
        return
    session_factory = (
        open_tenant_session(tenant_id=tenant_id, role="system")
        if tenant_id is not None
        else open_super_admin_session(reason="mark_outbox_failed_without_tenant")
    )
    async with session_factory as session:
        await OutboxService(session).mark_kafka_message_failed(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            error_message=error_message,
            dead=dead,
        )


async def _release_dispatch_lock(*, lock_key: str | None, lock_token: str | None) -> None:
    if not lock_key:
        return
    await CacheService().release_lock(lock_key, lock_token)


async def _release_tenant_job_counter(*, tenant_id: int | None) -> None:
    if tenant_id is None or tenant_id <= 0:
        return
    counter_key = f"analytics:tenant_jobs:{int(tenant_id)}"
    await CacheService().decrement_counter(counter_key)


async def enqueue_snapshot_rebuild(*, tenant_id: int, snapshot_type: str, ttl_seconds: int = 60, priority: int | None = None) -> bool:
    lock_key = f"analytics:lock:{int(tenant_id)}:{snapshot_type}"
    counter_key = f"analytics:tenant_jobs:{int(tenant_id)}"
    cache = CacheService()
    token = await cache.acquire_lock(lock_key, ttl=ttl_seconds)
    if token is None:
        return False
    current_jobs = await cache.increment_counter(counter_key, ttl=ttl_seconds)
    if current_jobs > MAX_ANALYTICS_JOBS_PER_TENANT:
        await cache.decrement_counter(counter_key)
        await cache.release_lock(lock_key, token)
        return False
    job_kwargs = {
        "tenant_id": int(tenant_id),
        "snapshot_type": str(snapshot_type),
        "dispatch_lock_key": lock_key,
        "dispatch_lock_token": token,
    }
    try:
        if priority is not None:
            rebuild_snapshot.apply_async(
                args=[int(tenant_id), str(snapshot_type)],
                kwargs={
                    "dispatch_lock_key": lock_key,
                    "dispatch_lock_token": token,
                },
                queue=ANALYTICS_QUEUE,
                priority=int(priority),
            )
            queued = True
        else:
            queued = enqueue_job_with_options(
                "jobs.rebuild_snapshot",
                kwargs=job_kwargs,
            )
    except Exception:
        logger.exception(
            "enqueue_snapshot_rebuild failed",
            extra={"tenant_id": tenant_id, "snapshot_type": snapshot_type, "priority": priority},
        )
        queued = False
    if not queued:
        await cache.decrement_counter(counter_key)
        await cache.release_lock(lock_key, token)
        return False
    return True


async def _create_analytics_dead_letter(
    *,
    job_name: str,
    tenant_id: int,
    payload: dict[str, Any],
    error_message: str,
    attempts: int,
) -> None:
    async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
        await DeadLetterRepository(session).create_event(
            tenant_id=tenant_id,
            source_event_id=None,
            source_type="analytics_job",
            event_type=job_name,
            payload_json=json.dumps(payload, separators=(",", ":"), sort_keys=True),
            error_message=error_message,
            attempts=attempts,
        )
        await session.commit()


def _analytics_retry_delay_seconds(attempt: int) -> int:
    settings = get_settings()
    return settings.analytics_rebuild_retry_base_delay_seconds * (2 ** max(attempt - 1, 0))


def _schedule_analytics_retry(
    *,
    job_name: str,
    delivery_attempt: int,
    kwargs: dict[str, Any],
) -> tuple[bool, int]:
    countdown = _analytics_retry_delay_seconds(delivery_attempt)
    queued = enqueue_job_with_options(job_name, kwargs=kwargs, countdown=countdown)
    return queued, countdown


async def _list_student_tenant_ids(*, limit: int) -> list[int]:
    async with open_super_admin_session(reason="list_student_tenant_ids") as session:
        rows = (
            await session.execute(
                select(UserTenantRole.tenant_id)
                .where(UserTenantRole.role == UserRole.student)
                .distinct()
                .limit(limit)
            )
        ).all()
        return [int(row.tenant_id) for row in rows]


async def _list_active_tenant_ids(*, limit: int, active_within_minutes: int = 5) -> list[int]:
    if limit <= 0:
        return []
    active_since = datetime.now(timezone.utc) - timedelta(minutes=max(active_within_minutes, 1))
    async with open_super_admin_session(reason="list_active_tenant_ids") as session:
        rows = (
            await session.execute(
                select(LearningEvent.tenant_id)
                .where(func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at) >= active_since)
                .group_by(LearningEvent.tenant_id)
                .order_by(func.max(func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at)).desc())
                .limit(limit)
            )
        ).all()
        return [int(row.tenant_id) for row in rows]


async def _run_generate_roadmap(user_id: int, tenant_id: int, goal_id: int, test_id: int) -> dict[str, Any]:
    async with open_tenant_session(tenant_id=tenant_id, role="system", actor_user_id=user_id) as session:
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


@_task(
    queue=CRITICAL_QUEUE,
    bind=True,
    name="jobs.generate_roadmap",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_roadmap(self=None, user_id: int = 0, tenant_id: int = 0, goal_id: int = 0, test_id: int = 0) -> dict[str, Any]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_generate_roadmap(user_id, tenant_id, goal_id, test_id))
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
    async with open_tenant_session(tenant_id=tenant_id, role="system", actor_user_id=user_id) as session:
        result = await DiagnosticService(session).get_result(test_id=test_id, user_id=user_id, tenant_id=tenant_id)
        topic_scores = result.get("topic_scores") or {}
        if not isinstance(topic_scores, dict):
            topic_scores = {}
        weak_topics = sorted([int(topic_id) for topic_id, score in topic_scores.items() if float(score) < 70.0])
        return {
            "test_id": test_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "topic_scores": topic_scores,
            "weak_topics": weak_topics,
        }


@_task(
    queue=CRITICAL_QUEUE,
    bind=True,
    name="jobs.analyze_diagnostic",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def analyze_diagnostic(self=None, test_id: int = 0, user_id: int = 0, tenant_id: int = 0) -> dict[str, Any]:
    _ = self
    try:
        result = _run_async(_run_analyze_diagnostic(test_id, user_id, tenant_id))
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


async def _run_process_mentor_chat(tenant_id: int, user_id: int, request_id: str) -> dict[str, Any]:
    async with open_tenant_session(tenant_id=tenant_id, role="system", actor_user_id=user_id) as session:
        repository = MentorChatRepository(session)

        outbound = await repository.get_by_request(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            direction="outbound",
        )
        # Idempotency: if a worker already produced the response, don't recompute.
        if outbound is not None and outbound.status in {"ready", "delivered", "acked"} and outbound.content:
            return {"status": "already_processed", "tenant_id": tenant_id, "user_id": user_id, "request_id": request_id}

        inbound = await repository.get_by_request(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            direction="inbound",
        )
        if inbound is None or not inbound.content:
            return {"status": "missing_inbound", "tenant_id": tenant_id, "user_id": user_id, "request_id": request_id}

        chat_history: list[dict[str, str]] = []
        if inbound.response_json:
            try:
                parsed = json.loads(inbound.response_json)
                if isinstance(parsed, dict) and isinstance(parsed.get("chat_history"), list):
                    chat_history = list(parsed["chat_history"])
            except json.JSONDecodeError:
                chat_history = []

        try:
            result = await MentorService(session=session).chat(
                message=inbound.content,
                user_id=user_id,
                tenant_id=tenant_id,
                chat_history=chat_history,
            )
            result["request_id"] = request_id
            outbound = await repository.upsert_message(
                tenant_id=tenant_id,
                user_id=user_id,
                request_id=request_id,
                direction="outbound",
                channel="queue",
                status="ready",
                content=str(result.get("reply") or ""),
                response_json=result,
            )
            await repository.mark_delivered(outbound)
            await session.commit()
            reply = str(result.get("reply") or "")
            if reply:
                for index in range(12, len(reply) + 12, 12):
                    await realtime_hub.send_user(
                        tenant_id,
                        user_id,
                        {
                            "type": "mentor.response.chunk",
                            "request_id": request_id,
                            "content": reply[:index],
                            "done": index >= len(reply),
                        },
                    )
                    await asyncio.sleep(0.02)
            await realtime_hub.send_user(
                tenant_id,
                user_id,
                {
                    "type": "mentor.response.ready",
                    "request_id": request_id,
                    "reply": reply,
                    "used_ai": bool(result.get("used_ai")),
                    "session_summary": result.get("session_summary", ""),
                    "provider": result.get("provider"),
                    "why_recommended": result.get("why_recommended", []),
                },
            )
            return {"status": "processed", "tenant_id": tenant_id, "user_id": user_id, "request_id": request_id}
        except Exception as exc:  # pragma: no cover
            # Best-effort persist failure state so status APIs can show progress.
            await repository.upsert_message(
                tenant_id=tenant_id,
                user_id=user_id,
                request_id=request_id,
                direction="outbound",
                channel="queue",
                status="failed",
                content="",
                response_json={"error": str(exc)},
            )
            await session.commit()
            return {"status": "failed", "tenant_id": tenant_id, "user_id": user_id, "request_id": request_id}


@_task(
    queue=AI_QUEUE,
    bind=True,
    name="jobs.process_mentor_chat",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_mentor_chat(self=None, tenant_id: int = 0, user_id: int = 0, request_id: str = "") -> dict[str, Any]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_process_mentor_chat(tenant_id, user_id, request_id))
        _record_task_duration("jobs.process_mentor_chat", "success", started_at)
        logger.info("process_mentor_chat completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.process_mentor_chat", "failed", started_at)
        logger.exception(
            "process_mentor_chat failed",
            extra={"tenant_id": tenant_id, "user_id": user_id, "request_id": request_id},
        )
        raise exc


async def _run_process_ai_request(tenant_id: int, user_id: int, request_id: str) -> dict[str, Any]:
    async with open_tenant_session(tenant_id=tenant_id, role="system", actor_user_id=user_id) as session:
        return await AIRequestService(session).process_request(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
        )


@_task(queue=AI_QUEUE, bind=True, name="jobs.process_ai_request", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_ai_request(self=None, tenant_id: int = 0, user_id: int = 0, request_id: str = "") -> dict[str, Any]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_process_ai_request(tenant_id, user_id, request_id))
        _record_task_duration("jobs.process_ai_request", str(result.get("status", "success")), started_at)
        logger.info(
            "process_ai_request completed",
            extra={"tenant_id": tenant_id, "user_id": user_id, "request_id": request_id, **result},
        )
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.process_ai_request", "failed", started_at)
        logger.exception("process_ai_request failed", extra={"tenant_id": tenant_id, "user_id": user_id, "request_id": request_id})
        raise exc


async def _run_process_learning_event(event_id: int, tenant_id: int) -> dict[str, Any]:
    async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
        event = await session.get(LearningEvent, event_id)
        if event is None:
            return {"status": "missing", "event_id": event_id}
        await MLPlatformService(session).build_feature_snapshot(user_id=event.user_id, tenant_id=event.tenant_id)
        return {"status": "processed", "event_id": event_id, "user_id": event.user_id, "tenant_id": event.tenant_id}


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.process_learning_event", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_learning_event(self=None, event_id: int = 0, tenant_id: int = 0, outbox_idempotency_key: str | None = None) -> dict[str, Any]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_process_learning_event(event_id, tenant_id))
        if str(result.get("status")) == "processed":
            _run_async(_mark_outbox_processed(tenant_id=tenant_id, idempotency_key=outbox_idempotency_key))
        else:
            _run_async(
                _mark_outbox_failed(
                    tenant_id=tenant_id,
                    idempotency_key=outbox_idempotency_key,
                    error_message=str(result.get("status", "unknown")),
                )
            )
        _record_task_duration("jobs.process_learning_event", "success", started_at)
        logger.info("process_learning_event completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _run_async(_mark_outbox_failed(tenant_id=tenant_id, idempotency_key=outbox_idempotency_key, error_message=str(exc)))
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


@_task(queue=OPS_QUEUE, bind=True, name="jobs.send_notifications")
def send_notifications(
    self=None,
    roadmap_steps: list[dict[str, Any]] | None = None,
    topic_scores: dict[int, float] | None = None,
    last_activity_at_iso: str | None = None,
) -> list[dict[str, str]]:
    _ = self
    roadmap_steps = roadmap_steps or []
    topic_scores = topic_scores or {}
    try:
        result = _run_async(_run_send_notifications(roadmap_steps, topic_scores, last_activity_at_iso))
        logger.info("send_notifications completed", extra={"count": len(result)})
        return result
    except Exception as exc:  # pragma: no cover
        logger.exception("send_notifications failed")
        raise exc


async def _run_send_email(to_email: str, subject: str, html_content: str, text_content: str) -> dict[str, str | bool]:
    service = EmailService()
    return await service.send(
        EmailPayload(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
    )


@_task(queue=OPS_QUEUE, bind=True, name="jobs.send_email", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_email(self=None, to_email: str = "", subject: str = "", html_content: str = "", text_content: str = "") -> dict[str, str | bool]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_send_email(to_email=to_email, subject=subject, html_content=html_content, text_content=text_content))
        _record_task_duration("jobs.send_email", "success", started_at)
        logger.info("send_email completed", extra={"to_email": to_email, "subject": subject, **result})
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.send_email", "failed", started_at)
        logger.exception("send_email failed", extra={"to_email": to_email, "subject": subject})
        raise exc


async def _run_generate_notifications(tenant_id: int | None = None, limit_users: int = 100) -> dict[str, int | None]:
    if tenant_id is not None:
        async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
            created = await NotificationService(session).generate_due_notifications(tenant_id=tenant_id, limit_users=limit_users)
            return {"created": created, "tenant_id": tenant_id}

    total_created = 0
    tenant_ids = await _list_student_tenant_ids(limit=limit_users)
    for current_tenant_id in tenant_ids:
        async with open_tenant_session(tenant_id=current_tenant_id, role="system") as session:
            total_created += await NotificationService(session).generate_due_notifications(
                tenant_id=current_tenant_id,
                limit_users=limit_users,
            )
    return {"created": total_created, "tenant_id": None}


@_task(queue=OPS_QUEUE, bind=True, name="jobs.generate_notifications", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def generate_notifications(self=None, tenant_id: int | None = None, limit_users: int = 100) -> dict[str, int | None]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_generate_notifications(tenant_id=tenant_id, limit_users=limit_users))
        _record_task_duration("jobs.generate_notifications", "success", started_at)
        logger.info(
            "generate_notifications completed",
            extra={
                "tenant_id": result.get("tenant_id"),
                "notifications_created": result.get("created", 0),
            },
        )
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.generate_notifications", "failed", started_at)
        logger.exception("generate_notifications failed", extra={"tenant_id": tenant_id, "limit_users": limit_users})
        raise exc


async def _run_decay_skill_vectors(tenant_id: int | None = None, inactive_days: int = 21) -> dict[str, int | None]:
    if tenant_id is not None:
        async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
            decayed = await SkillVectorService(session).decay_inactive_vectors(tenant_id=tenant_id, inactive_days=inactive_days)
            return {"decayed": decayed, "tenant_id": tenant_id}

    total_decayed = 0
    tenant_ids = await _list_student_tenant_ids(limit=get_settings().analytics_refresh_tenant_batch_size)
    for current_tenant_id in tenant_ids:
        async with open_tenant_session(tenant_id=current_tenant_id, role="system") as session:
            total_decayed += await SkillVectorService(session).decay_inactive_vectors(
                tenant_id=current_tenant_id,
                inactive_days=inactive_days,
            )
    return {"decayed": total_decayed, "tenant_id": None}


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.decay_skill_vectors", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def decay_skill_vectors(self=None, tenant_id: int | None = None, inactive_days: int = 21) -> dict[str, int | None]:
    _ = self
    try:
        result = _run_async(_run_decay_skill_vectors(tenant_id=tenant_id, inactive_days=inactive_days))
        logger.info("decay_skill_vectors completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        logger.exception("decay_skill_vectors failed", extra={"tenant_id": tenant_id, "inactive_days": inactive_days})
        raise exc


async def _run_process_outbox_events(limit: int = 100) -> dict[str, int]:
    async def _operation(session):
        sent = await OutboxService(session).flush_pending_events(limit=limit)
        return {"dispatched": sent}

    return await _run_global_super_admin_job(reason="process_outbox_events", operation=_operation)


@_task(queue=OPS_QUEUE, bind=True, name="jobs.process_outbox_events")
def process_outbox_events(self=None, limit: int = 100) -> dict[str, int]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_process_outbox_events(limit=limit))
        _record_task_duration("jobs.process_outbox_events", "success", started_at)
        logger.info("process_outbox_events completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.process_outbox_events", "failed", started_at)
        logger.exception("process_outbox_events failed", extra={"limit": limit})
        raise exc


async def _run_cleanup_outbox_events() -> dict[str, int]:
    return await _run_global_super_admin_job(
        reason="cleanup_outbox_events",
        operation=lambda session: OutboxService(session).cleanup_old_events(),
    )


@_task(queue=OPS_QUEUE, bind=True, name="jobs.cleanup_outbox_events")
def cleanup_outbox_events(self=None) -> dict[str, int]:
    _ = self
    try:
        result = _run_async(_run_cleanup_outbox_events())
        logger.info("cleanup_outbox_events completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        logger.exception("cleanup_outbox_events failed")
        raise exc


async def _run_refresh_outbox_metrics() -> dict[str, str]:
    async def _operation(session):
        await OutboxService(session).refresh_queue_depth_metrics()
        return {"status": "ok"}

    return await _run_global_super_admin_job(reason="refresh_outbox_metrics", operation=_operation)


@_task(queue=OPS_QUEUE, bind=True, name="jobs.refresh_outbox_metrics")
def refresh_outbox_metrics(self=None) -> dict[str, str]:
    _ = self
    try:
        result = _run_async(_run_refresh_outbox_metrics())
        logger.info("refresh_outbox_metrics completed")
        return result
    except Exception as exc:  # pragma: no cover
        logger.exception("refresh_outbox_metrics failed")
        raise exc


async def _run_recover_stuck_outbox_events(limit: int = 500) -> dict[str, int]:
    async def _operation(session):
        recovered = await OutboxService(session).recover_stuck_processing_events(limit=limit)
        return {"recovered": recovered}

    return await _run_global_super_admin_job(reason="recover_stuck_outbox_events", operation=_operation)


@_task(queue=OPS_QUEUE, bind=True, name="jobs.recover_stuck_outbox_events")
def recover_stuck_outbox_events(self=None, limit: int = 500) -> dict[str, int]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_recover_stuck_outbox_events(limit=limit))
        _record_task_duration("jobs.recover_stuck_outbox_events", "success", started_at)
        logger.info("recover_stuck_outbox_events completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.recover_stuck_outbox_events", "failed", started_at)
        logger.exception("recover_stuck_outbox_events failed", extra={"limit": limit})
        raise exc


async def _run_refresh_precomputed_analytics(tenant_id: int | None = None, limit_users: int = 250) -> dict[str, int | None]:
    refreshed_tenants = 0
    if tenant_id is not None:
        async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
            service = PrecomputedAnalyticsService(session)
            await service.refresh_scheduled_tenant_projections(tenant_id=tenant_id, limit_users=limit_users)
            await session.commit()
            refreshed_tenants = 1
    else:
        tenant_ids = await _list_student_tenant_ids(limit=limit_users)
        for current_tenant_id in tenant_ids:
            async with open_tenant_session(tenant_id=current_tenant_id, role="system") as session:
                service = PrecomputedAnalyticsService(session)
                await service.refresh_scheduled_tenant_projections(tenant_id=current_tenant_id, limit_users=limit_users)
                await session.commit()
            refreshed_tenants += 1
        async def _operation(session):
            service = PrecomputedAnalyticsService(session)
            await service.refresh_platform_overview()
            await session.commit()

        await _run_global_super_admin_job(reason="refresh_platform_overview", operation=_operation)
    return {"refreshed_tenants": refreshed_tenants, "tenant_id": tenant_id}


async def _run_refresh_active_tenant_analytics(
    limit_users: int = 50,
    tenant_limit: int = 25,
    active_within_minutes: int = 5,
) -> dict[str, int]:
    tenant_ids = await _list_active_tenant_ids(limit=tenant_limit, active_within_minutes=active_within_minutes)
    refreshed_tenants = 0
    refreshed_users = 0
    for tenant_id in tenant_ids:
        async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
            service = PrecomputedAnalyticsService(session)
            batch_result = await service.refresh_scheduled_tenant_projections(
                tenant_id=tenant_id,
                limit_users=limit_users,
            )
            await session.commit()
            refreshed_tenants += 1
            refreshed_users += int(batch_result["refreshed_users"])
    return {
        "refreshed_tenants": refreshed_tenants,
        "refreshed_users": refreshed_users,
    }


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.refresh_precomputed_analytics", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def refresh_precomputed_analytics(self=None, tenant_id: int | None = None, limit_users: int = 250) -> dict[str, int | None]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_refresh_precomputed_analytics(tenant_id=tenant_id, limit_users=limit_users))
        _record_task_duration("jobs.refresh_precomputed_analytics", "success", started_at)
        logger.info("refresh_precomputed_analytics completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.refresh_precomputed_analytics", "failed", started_at)
        logger.exception("refresh_precomputed_analytics failed", extra={"tenant_id": tenant_id})
        raise exc


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.refresh_active_tenant_analytics", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def refresh_active_tenant_analytics(
    self=None,
    limit_users: int = 50,
    tenant_limit: int = 25,
    active_within_minutes: int = 5,
) -> dict[str, int]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(
            _run_refresh_active_tenant_analytics(
                limit_users=limit_users,
                tenant_limit=tenant_limit,
                active_within_minutes=active_within_minutes,
            )
        )
        _record_task_duration("jobs.refresh_active_tenant_analytics", "success", started_at)
        logger.info("refresh_active_tenant_analytics completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.refresh_active_tenant_analytics", "failed", started_at)
        logger.exception(
            "refresh_active_tenant_analytics failed",
            extra={
                "limit_users": limit_users,
                "tenant_limit": tenant_limit,
                "active_within_minutes": active_within_minutes,
            },
        )
        raise exc


async def _run_refresh_user_projection(tenant_id: int, user_id: int, projection_type: str) -> dict[str, int | str]:
    async with open_tenant_session(tenant_id=tenant_id, role="system", actor_user_id=user_id) as session:
        service = PrecomputedAnalyticsService(session)
        if projection_type == "user_roadmap_stats":
            payload = await service.refresh_user_roadmap_stats(tenant_id=tenant_id, user_id=user_id)
        elif projection_type == "user_diagnostic_summary":
            payload = await service.refresh_user_diagnostic_summary(tenant_id=tenant_id, user_id=user_id)
        else:
            raise ValueError(f"Unsupported user projection type: {projection_type}")
        await session.commit()
        return {
            "status": "processed",
            "tenant_id": tenant_id,
            "user_id": user_id,
            "projection_type": projection_type,
            "subject_id": int(payload["user_id"]),
        }


async def _run_refresh_roadmap_progress_summary(tenant_id: int) -> dict[str, int | str]:
    async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
        analytics_service = AnalyticsService(session)
        learners = await analytics_service._roadmap_progress_rows(tenant_id=tenant_id)
        total = len(learners)
        average_completion_percent = round(sum(int(item["completion_percent"]) for item in learners) / max(total, 1)) if learners else 0
        average_mastery_percent = round(sum(int(item["mastery_percent"]) for item in learners) / max(total, 1)) if learners else 0
        payload = {
            "tenant_id": tenant_id,
            "student_count": total,
            "average_completion_percent": int(average_completion_percent),
            "average_mastery_percent": int(average_mastery_percent),
            "learners": learners,
        }
        await AnalyticsSnapshotService(session).write_snapshot(tenant_id, "roadmap_progress_summary", payload)
        return {"status": "processed", "tenant_id": tenant_id, "snapshot": "roadmap_progress_summary"}


async def _run_refresh_learner_intelligence_overview(tenant_id: int, user_id: int) -> dict[str, int | str]:
    async with open_tenant_session(tenant_id=tenant_id, role="system", actor_user_id=user_id) as session:
        payload = await SkillVectorService(session).aggregated_feature_payload(tenant_id=tenant_id, user_id=user_id)
        await AnalyticsSnapshotService(session).write_snapshot(
            tenant_id,
            "learner_intelligence_overview",
            {"tenant_id": tenant_id, "user_id": user_id, **payload},
            subject_id=user_id,
        )
        return {"status": "processed", "tenant_id": tenant_id, "user_id": user_id, "snapshot": "learner_intelligence_overview"}


async def _run_refresh_learning_trends(tenant_id: int) -> dict[str, int | str]:
    async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
        payload = await SkillVectorService(session).learning_trends(tenant_id=tenant_id)
        await AnalyticsSnapshotService(session).write_snapshot(
            tenant_id,
            "learning_trends",
            {"tenant_id": tenant_id, "points": payload},
        )
        return {"status": "processed", "tenant_id": tenant_id, "snapshot": "learning_trends", "point_count": len(payload)}


async def _run_refresh_retention_summary(tenant_id: int) -> dict[str, int | str]:
    async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
        payload = await RetentionService(session).tenant_retention_summary(tenant_id=tenant_id)
        await AnalyticsSnapshotService(session).write_snapshot(tenant_id, "tenant_retention_summary", payload)
        return {"status": "processed", "tenant_id": tenant_id, "snapshot": "tenant_retention_summary"}


async def _run_rebuild_snapshot(tenant_id: int, snapshot_type: str) -> dict[str, int | str]:
    """
    1. Fetch raw data
    2. Compute analytics
    3. Store using write_snapshot()
    """
    normalized = normalize_snapshot_type(snapshot_type)
    if normalized == INSTITUTION_DASHBOARD_SNAPSHOT:
        async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
            payload = await PrecomputedAnalyticsService(session).refresh_tenant_dashboard(tenant_id=tenant_id)
            await session.commit()
            return {"status": "processed", "tenant_id": tenant_id, "snapshot": normalized, "subject_id": 0}
    if normalized == TEACHER_DASHBOARD_SNAPSHOT:
        return await _run_refresh_roadmap_progress_summary(tenant_id)
    if normalized == USER_DASHBOARD_SNAPSHOT:
        raise ValueError("user_dashboard rebuild requires a user-scoped refresh task")
    if normalized == "roadmap_progress_summary":
        return await _run_refresh_roadmap_progress_summary(tenant_id)
    if normalized == "learning_trends":
        return await _run_refresh_learning_trends(tenant_id)
    if normalized == "tenant_retention_summary":
        return await _run_refresh_retention_summary(tenant_id)
    if normalized == SYSTEM_SUMMARY_SNAPSHOT:
        async with open_super_admin_session(reason="rebuild_system_summary_snapshot") as session:
            payload = await PrecomputedAnalyticsService(session).refresh_platform_overview()
            await session.commit()
            return {"status": "processed", "tenant_id": tenant_id, "snapshot": normalized, "subject_id": 0}
    raise ValueError(f"Unsupported snapshot_type: {snapshot_type}")


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.refresh_user_projection", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def refresh_user_projection(self=None, tenant_id: int = 0, user_id: int = 0, projection_type: str = "") -> dict[str, int | str]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_refresh_user_projection(tenant_id=tenant_id, user_id=user_id, projection_type=projection_type))
        _record_task_duration("jobs.refresh_user_projection", "success", started_at)
        logger.info("refresh_user_projection completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.refresh_user_projection", "failed", started_at)
        logger.exception(
            "refresh_user_projection failed",
            extra={"tenant_id": tenant_id, "user_id": user_id, "projection_type": projection_type},
        )
        raise exc


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.refresh_roadmap_progress_summary", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def refresh_roadmap_progress_summary(self=None, tenant_id: int = 0) -> dict[str, int | str]:
    _ = self
    return _run_async(_run_refresh_roadmap_progress_summary(tenant_id=tenant_id))


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.refresh_learner_intelligence_overview", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def refresh_learner_intelligence_overview(self=None, tenant_id: int = 0, user_id: int = 0) -> dict[str, int | str]:
    _ = self
    return _run_async(_run_refresh_learner_intelligence_overview(tenant_id=tenant_id, user_id=user_id))


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.refresh_learning_trends", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def refresh_learning_trends(self=None, tenant_id: int = 0) -> dict[str, int | str]:
    _ = self
    return _run_async(_run_refresh_learning_trends(tenant_id=tenant_id))


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.refresh_retention_summary", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def refresh_retention_summary(self=None, tenant_id: int = 0) -> dict[str, int | str]:
    _ = self
    return _run_async(_run_refresh_retention_summary(tenant_id=tenant_id))


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.rebuild_snapshot", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def rebuild_snapshot(
    self=None,
    tenant_id: int = 0,
    snapshot_type: str = "",
    dispatch_lock_key: str | None = None,
    dispatch_lock_token: str | None = None,
) -> dict[str, int | str]:
    _ = self
    try:
        result = _run_async(_run_rebuild_snapshot(tenant_id=tenant_id, snapshot_type=snapshot_type))
        _run_async(_release_dispatch_lock(lock_key=dispatch_lock_key, lock_token=dispatch_lock_token))
        _run_async(_release_tenant_job_counter(tenant_id=tenant_id))
        return result
    except Exception:
        _run_async(_release_dispatch_lock(lock_key=dispatch_lock_key, lock_token=dispatch_lock_token))
        _run_async(_release_tenant_job_counter(tenant_id=tenant_id))
        raise


async def _run_refresh_student_analytics(tenant_id: int, user_id: int) -> dict[str, int | str]:
    async with open_tenant_session(tenant_id=tenant_id, role="system", actor_user_id=user_id) as session:
        payload = await PrecomputedAnalyticsService(session).refresh_student_performance_analytics(
            tenant_id=tenant_id,
            user_id=user_id,
        )
        await session.commit()
        return {"status": "processed", "tenant_id": tenant_id, "user_id": user_id, "snapshot": "student_performance_analytics"}


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.refresh_student_analytics")
def refresh_student_analytics(
    self=None,
    tenant_id: int = 0,
    user_id: int = 0,
    delivery_attempt: int = 1,
    dispatch_lock_key: str | None = None,
    dispatch_lock_token: str | None = None,
) -> dict[str, int | str]:
    _ = self
    started_at = time.perf_counter()
    job_name = "jobs.refresh_student_analytics"
    try:
        result = _run_async(_run_refresh_student_analytics(tenant_id=tenant_id, user_id=user_id))
        _run_async(_release_dispatch_lock(lock_key=dispatch_lock_key, lock_token=dispatch_lock_token))
        analytics_rebuild_jobs_total.labels(job_name=job_name, status="processed").inc()
        _record_task_duration(job_name, "success", started_at)
        logger.info("refresh_student_analytics completed", extra={**result, "delivery_attempt": delivery_attempt})
        return result
    except Exception as exc:  # pragma: no cover
        max_attempts = get_settings().analytics_rebuild_max_attempts
        if delivery_attempt < max_attempts:
            queued, countdown = _schedule_analytics_retry(
                job_name=job_name,
                delivery_attempt=delivery_attempt,
                kwargs={
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "delivery_attempt": delivery_attempt + 1,
                    "dispatch_lock_key": dispatch_lock_key,
                    "dispatch_lock_token": dispatch_lock_token,
                },
            )
            if queued:
                analytics_rebuild_retries_total.labels(job_name=job_name).inc()
                analytics_rebuild_jobs_total.labels(job_name=job_name, status="retry_scheduled").inc()
                _record_task_duration(job_name, "retry_scheduled", started_at)
                logger.warning(
                    "refresh_student_analytics retry scheduled",
                    extra={
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "delivery_attempt": delivery_attempt,
                        "next_attempt": delivery_attempt + 1,
                        "countdown_seconds": countdown,
                        "error": str(exc),
                    },
                )
                return {
                    "status": "retry_scheduled",
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "delivery_attempt": delivery_attempt,
                    "next_attempt": delivery_attempt + 1,
                    "countdown_seconds": countdown,
                }
        _run_async(
            _create_analytics_dead_letter(
                job_name=job_name,
                tenant_id=tenant_id,
                payload={"tenant_id": tenant_id, "user_id": user_id},
                error_message=str(exc),
                attempts=delivery_attempt,
            )
        )
        _run_async(_release_dispatch_lock(lock_key=dispatch_lock_key, lock_token=dispatch_lock_token))
        analytics_rebuild_dead_total.labels(job_name=job_name).inc()
        analytics_rebuild_jobs_total.labels(job_name=job_name, status="dead").inc()
        _record_task_duration(job_name, "dead", started_at)
        logger.exception(
            "refresh_student_analytics failed permanently",
            extra={"tenant_id": tenant_id, "user_id": user_id, "delivery_attempt": delivery_attempt},
        )
        return {
            "status": "dead",
            "tenant_id": tenant_id,
            "user_id": user_id,
            "delivery_attempt": delivery_attempt,
            "error": str(exc),
        }


async def _run_refresh_topic_analytics(tenant_id: int, topic_id: int) -> dict[str, int | str]:
    async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
        topic = await session.get(Topic, topic_id)
        topic_name = str(getattr(topic, "name", f"Topic {topic_id}"))
        await PrecomputedAnalyticsService(session).refresh_topic_performance_analytics(
            tenant_id=tenant_id,
            topic_id=topic_id,
            topic_name=topic_name,
        )
        await session.commit()
        return {"status": "processed", "tenant_id": tenant_id, "topic_id": topic_id, "snapshot": "topic_performance_analytics"}


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.refresh_topic_analytics")
def refresh_topic_analytics(
    self=None,
    tenant_id: int = 0,
    topic_id: int = 0,
    delivery_attempt: int = 1,
    dispatch_lock_key: str | None = None,
    dispatch_lock_token: str | None = None,
) -> dict[str, int | str]:
    _ = self
    started_at = time.perf_counter()
    job_name = "jobs.refresh_topic_analytics"
    try:
        result = _run_async(_run_refresh_topic_analytics(tenant_id=tenant_id, topic_id=topic_id))
        _run_async(_release_dispatch_lock(lock_key=dispatch_lock_key, lock_token=dispatch_lock_token))
        analytics_rebuild_jobs_total.labels(job_name=job_name, status="processed").inc()
        _record_task_duration(job_name, "success", started_at)
        logger.info("refresh_topic_analytics completed", extra={**result, "delivery_attempt": delivery_attempt})
        return result
    except Exception as exc:  # pragma: no cover
        max_attempts = get_settings().analytics_rebuild_max_attempts
        if delivery_attempt < max_attempts:
            queued, countdown = _schedule_analytics_retry(
                job_name=job_name,
                delivery_attempt=delivery_attempt,
                kwargs={
                    "tenant_id": tenant_id,
                    "topic_id": topic_id,
                    "delivery_attempt": delivery_attempt + 1,
                    "dispatch_lock_key": dispatch_lock_key,
                    "dispatch_lock_token": dispatch_lock_token,
                },
            )
            if queued:
                analytics_rebuild_retries_total.labels(job_name=job_name).inc()
                analytics_rebuild_jobs_total.labels(job_name=job_name, status="retry_scheduled").inc()
                _record_task_duration(job_name, "retry_scheduled", started_at)
                logger.warning(
                    "refresh_topic_analytics retry scheduled",
                    extra={
                        "tenant_id": tenant_id,
                        "topic_id": topic_id,
                        "delivery_attempt": delivery_attempt,
                        "next_attempt": delivery_attempt + 1,
                        "countdown_seconds": countdown,
                        "error": str(exc),
                    },
                )
                return {
                    "status": "retry_scheduled",
                    "tenant_id": tenant_id,
                    "topic_id": topic_id,
                    "delivery_attempt": delivery_attempt,
                    "next_attempt": delivery_attempt + 1,
                    "countdown_seconds": countdown,
                }
        _run_async(
            _create_analytics_dead_letter(
                job_name=job_name,
                tenant_id=tenant_id,
                payload={"tenant_id": tenant_id, "topic_id": topic_id},
                error_message=str(exc),
                attempts=delivery_attempt,
            )
        )
        _run_async(_release_dispatch_lock(lock_key=dispatch_lock_key, lock_token=dispatch_lock_token))
        analytics_rebuild_dead_total.labels(job_name=job_name).inc()
        analytics_rebuild_jobs_total.labels(job_name=job_name, status="dead").inc()
        _record_task_duration(job_name, "dead", started_at)
        logger.exception(
            "refresh_topic_analytics failed permanently",
            extra={"tenant_id": tenant_id, "topic_id": topic_id, "delivery_attempt": delivery_attempt},
        )
        return {
            "status": "dead",
            "tenant_id": tenant_id,
            "topic_id": topic_id,
            "delivery_attempt": delivery_attempt,
            "error": str(exc),
        }


async def _run_process_notification_event(notification_id: int, tenant_id: int) -> dict[str, int | str]:
    async with open_tenant_session(tenant_id=tenant_id, role="system") as session:
        notification = await session.get(Notification, notification_id)
        if notification is None:
            return {"status": "missing", "notification_id": notification_id}
        return {"status": "processed", "notification_id": notification_id, "tenant_id": int(notification.tenant_id)}


@_task(queue=OPS_QUEUE, bind=True, name="jobs.process_notification_event", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_notification_event(self=None, notification_id: int = 0, tenant_id: int = 0, outbox_idempotency_key: str | None = None) -> dict[str, int | str]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_process_notification_event(notification_id, tenant_id))
        if str(result.get("status")) == "processed":
            _run_async(_mark_outbox_processed(tenant_id=tenant_id, idempotency_key=outbox_idempotency_key))
        else:
            _run_async(
                _mark_outbox_failed(
                    tenant_id=tenant_id,
                    idempotency_key=outbox_idempotency_key,
                    error_message=str(result.get("status", "unknown")),
                )
            )
        _record_task_duration("jobs.process_notification_event", "success", started_at)
        logger.info("process_notification_event completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _run_async(_mark_outbox_failed(tenant_id=tenant_id, idempotency_key=outbox_idempotency_key, error_message=str(exc)))
        _record_task_duration("jobs.process_notification_event", "failed", started_at)
        logger.exception("process_notification_event failed", extra={"notification_id": notification_id})
        raise exc


async def _run_process_analytics_event(tenant_id: int, snapshot_type: str, subject_id: int | None = None) -> dict[str, int | str | None]:
    return {"status": "processed", "tenant_id": tenant_id, "snapshot_type": snapshot_type, "subject_id": subject_id}


@_task(queue=ANALYTICS_QUEUE, bind=True, name="jobs.process_analytics_event", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_analytics_event(self=None, tenant_id: int = 0, snapshot_type: str = "", subject_id: int | None = None, outbox_idempotency_key: str | None = None) -> dict[str, int | str | None]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_process_analytics_event(tenant_id=tenant_id, snapshot_type=snapshot_type, subject_id=subject_id))
        if str(result.get("status")) == "processed":
            _run_async(_mark_outbox_processed(tenant_id=tenant_id, idempotency_key=outbox_idempotency_key))
        else:
            _run_async(
                _mark_outbox_failed(
                    tenant_id=tenant_id,
                    idempotency_key=outbox_idempotency_key,
                    error_message=str(result.get("status", "unknown")),
                )
            )
        _record_task_duration("jobs.process_analytics_event", "success", started_at)
        logger.info("process_analytics_event completed", extra=result)
        return result
    except Exception as exc:  # pragma: no cover
        _run_async(_mark_outbox_failed(tenant_id=tenant_id, idempotency_key=outbox_idempotency_key, error_message=str(exc)))
        _record_task_duration("jobs.process_analytics_event", "failed", started_at)
        logger.exception("process_analytics_event failed", extra={"tenant_id": tenant_id, "snapshot_type": snapshot_type})
        raise exc


async def _run_process_domain_event(envelope: dict[str, Any], delivery_attempt: int = 1, outbox_idempotency_key: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    async with open_tenant_session(tenant_id=int(envelope["tenant_id"]), role="system", actor_user_id=envelope.get("user_id")) as session:
        service = DomainEventConsumerService(session)
        state, is_duplicate = await service.begin_processing(envelope=envelope, attempt=delivery_attempt)
        await session.commit()
        if is_duplicate:
            event_name = str(envelope["event_name"])
            if outbox_idempotency_key:
                await OutboxService(session).mark_kafka_message_processed(
                    tenant_id=envelope.get("tenant_id"),
                    idempotency_key=outbox_idempotency_key,
                )
                await session.commit()
            domain_event_consumer_total.labels(event_name=event_name, status="duplicate").inc()
            return {
                "status": "duplicate",
                "event_name": event_name,
                "message_id": str(envelope["message_id"]),
                "delivery_attempt": delivery_attempt,
            }

        event_name = str(envelope["event_name"])
        try:
            result = await service.handle_event(envelope=envelope)
            await service.mark_success(state, attempt=delivery_attempt)
            if outbox_idempotency_key:
                await OutboxService(session).mark_kafka_message_processed(
                    tenant_id=envelope.get("tenant_id"),
                    idempotency_key=outbox_idempotency_key,
                )
            await session.commit()
            domain_event_consumer_total.labels(event_name=event_name, status="processed").inc()
            return {
                "status": "processed",
                "event_name": event_name,
                "message_id": str(envelope["message_id"]),
                "delivery_attempt": delivery_attempt,
                **result,
            }
        except Exception as exc:
            await session.rollback()
            state = await service.repository.get_or_create(
                consumer_name=service.CONSUMER_NAME,
                event_name=event_name,
                message_id=str(envelope["message_id"]),
                tenant_id=envelope.get("tenant_id"),
            )
            is_dead = delivery_attempt >= settings.event_consumer_max_attempts
            await service.mark_failure(state, attempt=delivery_attempt, error_message=str(exc), dead=is_dead)
            if outbox_idempotency_key:
                await OutboxService(session).mark_kafka_message_failed(
                    tenant_id=envelope.get("tenant_id"),
                    idempotency_key=outbox_idempotency_key,
                    error_message=str(exc),
                    dead=is_dead,
                )
            if is_dead:
                await DeadLetterRepository(session).create_event(
                    tenant_id=envelope.get("tenant_id"),
                    source_event_id=None,
                    source_type="consumer",
                    event_type=event_name,
                    payload_json=json.dumps(envelope, separators=(",", ":"), sort_keys=True),
                    error_message=str(exc),
                    attempts=delivery_attempt,
                )
            await session.commit()
            domain_event_consumer_total.labels(event_name=event_name, status="dead" if is_dead else "failed").inc()
            return {
                "status": "dead" if is_dead else "failed",
                "event_name": event_name,
                "message_id": str(envelope["message_id"]),
                "delivery_attempt": delivery_attempt,
                "error": str(exc),
            }


@_task(queue=CRITICAL_QUEUE, bind=True, name="jobs.process_domain_event")
def process_domain_event(self=None, envelope: dict[str, Any] | None = None, delivery_attempt: int = 1, outbox_idempotency_key: str | None = None) -> dict[str, Any]:
    _ = self
    envelope = envelope or {}
    started_at = time.perf_counter()
    result = _run_async(
        _run_process_domain_event(
            envelope=envelope,
            delivery_attempt=delivery_attempt,
            outbox_idempotency_key=outbox_idempotency_key,
        )
    )
    event_name = str(envelope.get("event_name", "unknown"))
    if result["status"] == "failed":
        delay_seconds = get_settings().event_consumer_retry_base_delay_seconds * (2 ** max(delivery_attempt - 1, 0))
        enqueue_job_with_options(
            "jobs.process_domain_event",
            kwargs={
                "envelope": envelope,
                "delivery_attempt": delivery_attempt + 1,
                "outbox_idempotency_key": outbox_idempotency_key,
            },
            countdown=delay_seconds,
        )
        domain_event_retry_total.labels(event_name=event_name).inc()
        _record_task_duration("jobs.process_domain_event", "retry_scheduled", started_at)
        logger.warning(
            "process_domain_event retry scheduled",
            extra={
                "event_name": event_name,
                "message_id": envelope.get("message_id"),
                "delivery_attempt": delivery_attempt,
                "next_attempt": delivery_attempt + 1,
                "countdown_seconds": delay_seconds,
                "error": result.get("error"),
            },
        )
        return {**result, "status": "retry_scheduled", "next_attempt": delivery_attempt + 1, "countdown_seconds": delay_seconds}
    _record_task_duration("jobs.process_domain_event", result["status"], started_at)
    log_method = logger.info if result["status"] in {"processed", "duplicate"} else logger.error
    log_method(
        "process_domain_event completed",
        extra={
            "event_name": event_name,
            "message_id": envelope.get("message_id"),
            "delivery_attempt": delivery_attempt,
            "status": result["status"],
            "error": result.get("error"),
        },
    )
    return result


async def _run_consume_kafka_events(limit: int = 100) -> dict[str, int]:
    if not get_settings().kafka_enabled:
        return {"processed": 0, "duplicate": 0, "failed": 0}
    return await _run_global_super_admin_job(
        reason="consume_kafka_events",
        operation=lambda session: KafkaConsumerService(
            session,
            consumer_group="learning-platform-celery",
        ).poll_and_process(max_records=limit),
    )


@_task(queue=OPS_QUEUE, bind=True, name="jobs.consume_kafka_events", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def consume_kafka_events(self=None, limit: int = 100) -> dict[str, int]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_consume_kafka_events(limit=limit))
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
    return await _run_global_super_admin_job(
        reason="replay_kafka_topic",
        operation=lambda session: KafkaConsumerService(
            session,
            consumer_group="learning-platform-replay",
        ).replay_from_offset(topic=topic, partition=partition, offset=offset, max_records=limit),
    )


@_task(queue=OPS_QUEUE, bind=True, name="jobs.replay_kafka_topic", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def replay_kafka_topic(self=None, topic: str = "", partition: int = 0, offset: int = 0, limit: int = 100) -> dict[str, int]:
    _ = self
    started_at = time.perf_counter()
    try:
        result = _run_async(_run_replay_kafka_topic(topic=topic, partition=partition, offset=offset, limit=limit))
        _record_task_duration("jobs.replay_kafka_topic", "success", started_at)
        logger.info("replay_kafka_topic completed", extra={"topic": topic, "partition": partition, "offset": offset, **result})
        return result
    except Exception as exc:  # pragma: no cover
        _record_task_duration("jobs.replay_kafka_topic", "failed", started_at)
        logger.exception("replay_kafka_topic failed", extra={"topic": topic, "partition": partition, "offset": offset})
        raise exc
