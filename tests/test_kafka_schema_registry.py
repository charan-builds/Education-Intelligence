import pytest

from app.events.schema_registry import EventSchemaValidationError, validate_event_envelope


def test_validate_event_envelope_accepts_learning_event():
    validate_event_envelope(
        {
            "message_id": "m1",
            "topic": "learning_events",
            "event_name": "learning_event.recorded",
            "schema_version": "v1",
            "partition_key": "1:2",
            "idempotency_key": "abc",
            "occurred_at": "2026-03-25T00:00:00+00:00",
            "payload": {"event_id": 1, "event_type": "question_answered", "tenant_id": 1, "user_id": 2},
        }
    )


def test_validate_event_envelope_rejects_missing_payload_field():
    with pytest.raises(EventSchemaValidationError):
        validate_event_envelope(
            {
                "message_id": "m1",
                "topic": "learning_events",
                "event_name": "learning_event.recorded",
                "schema_version": "v1",
                "partition_key": "1:2",
                "idempotency_key": "abc",
                "occurred_at": "2026-03-25T00:00:00+00:00",
                "payload": {"event_id": 1, "event_type": "question_answered", "tenant_id": 1},
            }
        )
