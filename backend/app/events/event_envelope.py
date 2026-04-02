from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(slots=True)
class EventEnvelope:
    topic: str
    event_name: str
    schema_version: str
    tenant_id: int | None
    user_id: int | None
    payload: dict
    partition_key: str
    idempotency_key: str
    message_id: str = field(default_factory=lambda: uuid4().hex)
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trace_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
