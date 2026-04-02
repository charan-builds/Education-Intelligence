from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from app.infrastructure.jobs.celery_app import celery_app

logger = logging.getLogger("learning_platform.jobs.dispatcher")


def enqueue_job(task_name: str, args: Sequence[Any] | None = None, kwargs: dict[str, Any] | None = None) -> bool:
    try:
        celery_app.send_task(task_name, args=list(args or []), kwargs=kwargs or {})
        return True
    except Exception:
        # Queue outages must never break request flow.
        logger.exception("Failed to enqueue job", extra={"task_name": task_name})
        return False


def enqueue_job_with_options(
    task_name: str,
    *,
    args: Sequence[Any] | None = None,
    kwargs: dict[str, Any] | None = None,
    countdown: int | None = None,
) -> bool:
    try:
        options: dict[str, Any] = {}
        if countdown is not None:
            options["countdown"] = int(countdown)
        celery_app.send_task(task_name, args=list(args or []), kwargs=kwargs or {}, **options)
        return True
    except Exception:
        logger.exception("Failed to enqueue job", extra={"task_name": task_name, "countdown": countdown})
        return False
