from __future__ import annotations

from contextlib import suppress

from app.core.config import get_settings

try:  # pragma: no cover
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
except Exception:  # pragma: no cover
    trace = None  # type: ignore
    OTLPSpanExporter = None  # type: ignore
    Resource = None  # type: ignore
    TracerProvider = None  # type: ignore
    BatchSpanProcessor = None  # type: ignore


def configure_tracing() -> None:
    settings = get_settings()
    if not settings.tracing_enabled or trace is None or TracerProvider is None or Resource is None:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": settings.tracing_service_name}))
    if settings.tracing_exporter_otlp_endpoint and OTLPSpanExporter is not None and BatchSpanProcessor is not None:
        exporter = OTLPSpanExporter(endpoint=settings.tracing_exporter_otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def get_tracer(name: str):
    if trace is None:  # pragma: no cover
        return None
    with suppress(Exception):
        return trace.get_tracer(name)
    return None
