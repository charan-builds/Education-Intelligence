import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.core.config import get_settings

SERVICE_NAME = "learning-platform"
LOGGER_NAME = "learning_platform"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extra_payload = getattr(record, "log_data", None)
        if isinstance(extra_payload, dict):
            payload.update(extra_payload)

        return json.dumps(payload, default=str)


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    settings = get_settings()
    if settings.audit_log_file_path:
        log_path = Path(settings.audit_log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=settings.audit_log_max_bytes,
            backupCount=settings.audit_log_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    return logger


def bind_log_data(**kwargs: Any) -> dict[str, dict[str, Any]]:
    return {"log_data": kwargs}
