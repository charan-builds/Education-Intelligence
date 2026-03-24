from celery import Celery

from app.core.config import get_settings

settings = get_settings()

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
    beat_schedule={
        "process-outbox-events-every-minute": {
            "task": "jobs.process_outbox_events",
            "schedule": 60.0,
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
    },
)

celery_app.autodiscover_tasks(["app.infrastructure.jobs"])
