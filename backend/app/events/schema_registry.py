from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class EventSchemaValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EventSchemaDefinition:
    event_name: str
    schema_version: str
    required_payload_fields: tuple[str, ...]


SCHEMA_DEFINITIONS: dict[tuple[str, str], EventSchemaDefinition] = {
    ("learning_event.recorded", "v1"): EventSchemaDefinition(
        event_name="learning_event.recorded",
        schema_version="v1",
        required_payload_fields=("event_id", "event_type", "tenant_id", "user_id"),
    ),
    ("notification.created", "v1"): EventSchemaDefinition(
        event_name="notification.created",
        schema_version="v1",
        required_payload_fields=("notification_id", "tenant_id", "user_id", "notification_type"),
    ),
    ("analytics.snapshot_refreshed", "v1"): EventSchemaDefinition(
        event_name="analytics.snapshot_refreshed",
        schema_version="v1",
        required_payload_fields=("snapshot_type", "tenant_id", "window_start", "window_end"),
    ),
}


def validate_event_envelope(payload: dict[str, Any]) -> None:
    required_envelope_fields = (
        "message_id",
        "topic",
        "event_name",
        "schema_version",
        "partition_key",
        "idempotency_key",
        "occurred_at",
        "payload",
    )
    for field_name in required_envelope_fields:
        if field_name not in payload:
            raise EventSchemaValidationError(f"Missing envelope field: {field_name}")
    if not isinstance(payload["payload"], dict):
        raise EventSchemaValidationError("Envelope payload must be an object")
    schema = SCHEMA_DEFINITIONS.get((str(payload["event_name"]), str(payload["schema_version"])))
    if schema is None:
        raise EventSchemaValidationError(
            f"Unsupported event schema: {payload['event_name']}@{payload['schema_version']}"
        )
    for field_name in schema.required_payload_fields:
        if field_name not in payload["payload"]:
            raise EventSchemaValidationError(f"Missing payload field: {field_name}")
