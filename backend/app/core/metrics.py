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

requests_in_flight = Gauge(
    "requests_in_flight",
    "Current in-flight HTTP requests",
    ["method"],
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

outbox_processed_total = Counter(
    "outbox_processed_total",
    "Total outbox events confirmed as successfully processed by a consumer",
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

cache_operations_total = Counter(
    "cache_operations_total",
    "Cache operation counts by operation and result",
    ["operation", "result"],
)

ai_requests_total = Counter(
    "ai_requests_total",
    "AI request outcomes by endpoint, provider, and outcome",
    ["endpoint", "provider", "outcome"],
)

ai_request_latency_seconds = Histogram(
    "ai_request_latency_seconds",
    "AI request latency in seconds by endpoint and provider",
    ["endpoint", "provider"],
)

learning_events_total = Counter(
    "learning_events_total",
    "Learning event ingestion outcomes",
    ["event_type", "result"],
)

websocket_connections_active = Gauge(
    "websocket_connections_active",
    "Active websocket connections by tenant",
    ["tenant_id"],
)

websocket_messages_total = Counter(
    "websocket_messages_total",
    "Websocket message delivery totals",
    ["direction", "result"],
)

websocket_backpressure_total = Counter(
    "websocket_backpressure_total",
    "Websocket backpressure drops",
    ["tenant_id"],
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
)

db_slow_queries_total = Counter(
    "db_slow_queries_total",
    "Database slow query detections",
    ["operation"],
)

event_processing_duration_seconds = Histogram(
    "event_processing_duration_seconds",
    "Event and background task processing duration in seconds",
    ["task_name", "status"],
)

domain_event_consumer_total = Counter(
    "domain_event_consumer_total",
    "Domain event consumer outcomes by event and status",
    ["event_name", "status"],
)

domain_event_retry_total = Counter(
    "domain_event_retry_total",
    "Domain event retries scheduled by event name",
    ["event_name"],
)

queue_wait_duration_seconds = Histogram(
    "queue_wait_duration_seconds",
    "Time a task spent queued before execution",
    ["task_name"],
)

task_retries_total = Counter(
    "task_retries_total",
    "Background task retries",
    ["task_name"],
)

analytics_rebuild_jobs_total = Counter(
    "analytics_rebuild_jobs_total",
    "Analytics rebuild job outcomes by job name and status",
    ["job_name", "status"],
)

analytics_rebuild_retries_total = Counter(
    "analytics_rebuild_retries_total",
    "Analytics rebuild retries scheduled by job name",
    ["job_name"],
)

analytics_rebuild_dead_total = Counter(
    "analytics_rebuild_dead_total",
    "Analytics rebuild jobs moved to dead letter by job name",
    ["job_name"],
)

super_admin_sessions_total = Counter(
    "super_admin_sessions_total",
    "Super-admin database sessions opened, labeled by explicit reason",
    ["reason"],
)

super_admin_sessions_active = Gauge(
    "super_admin_sessions_active",
    "Currently active super-admin database sessions",
    ["reason"],
)

circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state by dependency",
    ["dependency"],
)

metrics_router = APIRouter()


@metrics_router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
