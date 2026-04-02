import importlib
from types import SimpleNamespace

from app.infrastructure.jobs.celery_app import attach_publish_timestamp, record_queue_wait, record_task_retry
from app.infrastructure.jobs.tasks import _run_async

celery_app_module = importlib.import_module("app.infrastructure.jobs.celery_app")


class _MetricRecorder:
    def __init__(self) -> None:
        self.observations: list[tuple[dict, float]] = []
        self.increments: list[dict] = []

    def labels(self, **kwargs):
        recorder = self

        class _BoundMetric:
            def observe(self, value: float):
                recorder.observations.append((kwargs, value))

            def inc(self, amount: float = 1.0):
                recorder.increments.append(kwargs | {"amount": amount})

        return _BoundMetric()


def test_attach_publish_timestamp_adds_header():
    headers: dict[str, int] = {}
    attach_publish_timestamp(headers=headers)
    assert isinstance(headers["published_at_epoch_ms"], int)


def test_record_queue_wait_observes_latency(monkeypatch):
    metric = _MetricRecorder()
    monkeypatch.setattr(celery_app_module, "queue_wait_duration_seconds", metric)
    monkeypatch.setattr("time.time", lambda: 10.0)

    task = SimpleNamespace(
        name="jobs.process_mentor_chat",
        request=SimpleNamespace(headers={"published_at_epoch_ms": 9200}),
    )

    record_queue_wait(task=task)

    assert metric.observations
    labels, value = metric.observations[0]
    assert labels == {"task_name": "jobs.process_mentor_chat"}
    assert value == 0.8


def test_record_task_retry_increments_counter(monkeypatch):
    metric = _MetricRecorder()
    monkeypatch.setattr(celery_app_module, "task_retries_total", metric)

    record_task_retry(request=SimpleNamespace(task="jobs.generate_roadmap"))

    assert metric.increments == [{"task_name": "jobs.generate_roadmap", "amount": 1.0}]


def test_run_async_executes_coroutines_safely_per_call():
    first = _run_async(_return_marker("first"))
    second = _run_async(_return_marker("second"))

    assert first == "first"
    assert second == "second"


async def _return_marker(value: str) -> str:
    return value
