import json

from app.application.services import kafka_consumer_service
from app.infrastructure.jobs import tasks


def test_process_domain_event_schedules_retry(monkeypatch):
    envelope = {
        "message_id": "message-1",
        "topic": "learning_events.v1",
        "event_name": "diagnostic_completed",
        "schema_version": "v1",
        "partition_key": "1:2",
        "idempotency_key": "abc",
        "occurred_at": "2026-04-02T00:00:00+00:00",
        "tenant_id": 1,
        "user_id": 2,
        "payload": {
            "event_id": 10,
            "diagnostic_test_id": 20,
            "goal_id": 30,
            "tenant_id": 1,
            "user_id": 2,
        },
    }

    monkeypatch.setattr(
        tasks,
        "_run_async",
        lambda coro: (coro.close(), {"status": "failed", "event_name": "diagnostic_completed", "message_id": "message-1", "delivery_attempt": 1, "error": "boom"})[1],
    )
    monkeypatch.setattr(tasks, "_record_task_duration", lambda *args, **kwargs: None)
    scheduled = {}
    monkeypatch.setattr(
        tasks,
        "enqueue_job_with_options",
        lambda task_name, *, args=None, kwargs=None, countdown=None: scheduled.update(
            {"task_name": task_name, "args": args, "kwargs": kwargs, "countdown": countdown}
        )
        or True,
    )

    result = tasks.process_domain_event(envelope=envelope, delivery_attempt=1)

    assert result["status"] == "retry_scheduled"
    assert scheduled["task_name"] == "jobs.process_domain_event"
    assert scheduled["kwargs"]["delivery_attempt"] == 2
    assert scheduled["kwargs"]["envelope"]["message_id"] == "message-1"
    assert scheduled["kwargs"]["outbox_idempotency_key"] is None


def test_kafka_consumer_dispatches_domain_events_to_domain_worker(monkeypatch):
    dispatched = []

    def _fake_enqueue(task_name, args=None, kwargs=None):
        dispatched.append((task_name, args, kwargs))
        return True

    service = kafka_consumer_service.KafkaConsumerService.__new__(kafka_consumer_service.KafkaConsumerService)
    service.settings = type(
        "_Settings",
        (),
        {
            "kafka_topic_learning_events": "learning_events.v1",
            "kafka_topic_notifications": "notifications.v1",
            "kafka_topic_analytics": "analytics.v1",
        },
    )()
    monkeypatch.setattr(kafka_consumer_service, "enqueue_job", _fake_enqueue)

    payload = json.loads(
        json.dumps(
            {
                "message_id": "message-2",
                "topic": "learning_events.v1",
                "event_name": "roadmap_generated",
                "schema_version": "v1",
                "partition_key": "1:2",
                "idempotency_key": "idem-2",
                "occurred_at": "2026-04-02T00:00:00+00:00",
                "tenant_id": 1,
                "user_id": 2,
                "payload": {
                    "event_id": 11,
                    "roadmap_id": 21,
                    "diagnostic_test_id": 31,
                    "goal_id": 41,
                    "tenant_id": 1,
                    "user_id": 2,
                },
            }
        )
    )

    service._dispatch_to_celery(topic="learning_events.v1", payload=payload)

    assert dispatched == [
        (
            "jobs.process_domain_event",
            None,
            {"envelope": payload, "delivery_attempt": 1, "outbox_idempotency_key": "idem-2"},
        )
    ]
