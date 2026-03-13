from fastapi import APIRouter, Response

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
except Exception:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    class _NoopMetric:
        def labels(self, **kwargs):
            return self

        def inc(self, amount: float = 1.0):
            return None

        def observe(self, amount: float):
            return None

        def set(self, value: float):
            return None

    def Counter(*args, **kwargs):  # type: ignore
        return _NoopMetric()

    def Histogram(*args, **kwargs):  # type: ignore
        return _NoopMetric()

    def Gauge(*args, **kwargs):  # type: ignore
        return _NoopMetric()

    def generate_latest() -> bytes:  # type: ignore
        return b""

total_requests = Counter(
    "total_requests",
    "Total HTTP requests",
    ["endpoint", "method", "status_code"],
)

request_duration = Histogram(
    "request_duration",
    "HTTP request duration in seconds",
    ["endpoint", "method", "status_code"],
)

error_count = Counter(
    "error_count",
    "Total HTTP errors",
    ["endpoint", "method", "status_code"],
)

outbox_dispatched_total = Counter(
    "outbox_dispatched_total",
    "Total outbox events successfully dispatched to queue",
)

outbox_failed_total = Counter(
    "outbox_failed_total",
    "Total outbox dispatch failures",
)

outbox_dead_total = Counter(
    "outbox_dead_total",
    "Total outbox events moved to dead-letter status",
)

outbox_cleanup_removed_total = Counter(
    "outbox_cleanup_removed_total",
    "Total outbox rows removed by cleanup task",
    ["status"],
)

outbox_recovered_total = Counter(
    "outbox_recovered_total",
    "Total outbox events recovered from stuck processing state",
)

outbox_queue_depth = Gauge(
    "outbox_queue_depth",
    "Current outbox queue depth by status",
    ["status"],
)

metrics_router = APIRouter()


@metrics_router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
