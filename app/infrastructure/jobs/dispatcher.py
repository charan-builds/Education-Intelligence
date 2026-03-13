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
