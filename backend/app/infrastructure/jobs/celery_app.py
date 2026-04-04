import time

from celery import Celery
from celery.signals import before_task_publish, task_failure, task_postrun, task_prerun, task_retry
from kombu import Exchange, Queue

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import queue_wait_duration_seconds, task_retries_total

settings = get_settings()
logger = get_logger()

CELERY_TASK_QUEUES = (
    Queue("critical", Exchange("critical"), routing_key="critical.#"),
    Queue("analytics", Exchange("analytics"), routing_key="analytics.#"),
    Queue("ai", Exchange("ai"), routing_key="ai.#"),
    Queue("ops", Exchange("ops"), routing_key="ops.#"),
)

CELERY_TASK_DEFAULT_QUEUE = "critical"

CELERY_TASK_ROUTES = {
    "app.application.services.diagnostic_service.*": {"queue": "critical"},
    "app.application.services.roadmap_service.*": {"queue": "critical"},
    "app.application.services.precomputed_analytics_service.*": {"queue": "analytics"},
    "app.application.services.ai_execution_service.*": {"queue": "ai"},
    "app.application.services.mentor_ai_service.*": {"queue": "ai"},
    "app.infrastructure.jobs.tasks.*": {"queue": "ops"},
}

celery_app = Celery(
    "learning_platform",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    result_expires=3600,
    task_queues=CELERY_TASK_QUEUES,
    task_default_queue=CELERY_TASK_DEFAULT_QUEUE,
    task_routes=CELERY_TASK_ROUTES,
    beat_schedule={
        "process-outbox-events-every-minute": {
            "task": "jobs.process_outbox_events",
            "schedule": 60.0,
            "kwargs": {"limit": 200},
        },
        "consume-kafka-events-every-10s": {
            "task": "jobs.consume_kafka_events",
            "schedule": 10.0,
            "kwargs": {"limit": 200},
        },
        "cleanup-outbox-events-daily": {
            "task": "jobs.cleanup_outbox_events",
            "schedule": 86400.0,
        },
        "refresh-outbox-metrics-every-minute": {
            "task": "jobs.refresh_outbox_metrics",
            "schedule": 60.0,
        },
        "recover-stuck-outbox-events-every-5m": {
            "task": "jobs.recover_stuck_outbox_events",
            "schedule": 300.0,
            "kwargs": {"limit": 500},
        },
        "generate-notifications-every-10m": {
            "task": "jobs.generate_notifications",
            "schedule": 600.0,
            "kwargs": {"limit_users": 200},
        },
        "decay-skill-vectors-daily": {
            "task": "jobs.decay_skill_vectors",
            "schedule": 86400.0,
            "kwargs": {"inactive_days": 21},
        },
        "refresh-active-tenant-analytics-every-5m": {
            "task": "jobs.refresh_active_tenant_analytics",
            "schedule": 300.0,
            "kwargs": {"limit_users": 50, "tenant_limit": 25, "active_within_minutes": 5},
            "options": {"queue": "analytics"},
        },
        "refresh-precomputed-analytics-hourly": {
            "task": "jobs.refresh_precomputed_analytics",
            "schedule": 3600.0,
            "kwargs": {"limit_users": 250},
            "options": {"queue": "analytics", "priority": 1},
        },
    },
)

celery_app.autodiscover_tasks(["app.infrastructure.jobs"])


@before_task_publish.connect
def attach_publish_timestamp(headers=None, **_kwargs):  # pragma: no cover
    if headers is not None and headers.get("published_at_epoch_ms") is None:
        headers["published_at_epoch_ms"] = int(time.time() * 1000)
        logger.info(
            "celery task published",
            extra={"log_data": {"task_headers": {"id": headers.get("id"), "task": headers.get("task")}}},
        )


@task_prerun.connect
def record_queue_wait(task=None, **_kwargs):  # pragma: no cover
    if task is None or getattr(task, "request", None) is None:
        return
    raw_published_at = getattr(task.request, "headers", {}).get("published_at_epoch_ms")
    try:
        published_at_ms = int(raw_published_at)
    except (TypeError, ValueError):
        return
    wait_seconds = max((time.time() * 1000 - published_at_ms) / 1000, 0.0)
    queue_wait_duration_seconds.labels(task_name=task.name or "unknown").observe(wait_seconds)
    logger.info(
        "celery task started",
        extra={
            "log_data": {
                "task_id": getattr(task.request, "id", None),
                "task_name": task.name or "unknown",
                "queue_wait_seconds": round(wait_seconds, 4),
            }
        },
    )


@task_retry.connect
def record_task_retry(request=None, **_kwargs):  # pragma: no cover
    task_name = getattr(request, "task", None) or "unknown"
    task_retries_total.labels(task_name=task_name).inc()
    logger.warning(
        "celery task retry scheduled",
        extra={"log_data": {"task_id": getattr(request, "id", None), "task_name": task_name}},
    )


@task_postrun.connect
def log_task_postrun(task_id=None, task=None, state=None, retval=None, **_kwargs):  # pragma: no cover
    logger.info(
        "celery task completed",
        extra={
            "log_data": {
                "task_id": task_id,
                "task_name": getattr(task, "name", "unknown"),
                "state": state,
                "result_type": type(retval).__name__ if retval is not None else None,
            }
        },
    )


@task_failure.connect
def log_task_failure(task_id=None, exception=None, sender=None, **_kwargs):  # pragma: no cover
    logger.error(
        "celery task failed",
        extra={
            "log_data": {
                "task_id": task_id,
                "task_name": getattr(sender, "name", "unknown"),
                "error_type": type(exception).__name__ if exception is not None else None,
                "error_message": str(exception) if exception is not None else None,
            }
        },
    )
