from celery.exceptions import CeleryError
from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import get_settings
from app.core.metrics import metrics_router
from app.core.security_middleware import register_security_middleware
from app.core.tracing import configure_tracing
from app.infrastructure.cache.redis_client import get_redis_client
from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.jobs.celery_app import celery_app
from app.presentation.api_router import api_router
from app.presentation.error_handlers import register_exception_handlers
from app.presentation.middleware.logging_middleware import RequestLoggingMiddleware
from app.presentation.middleware.rate_limiter import register_rate_limiter
from app.realtime.distributed_bus import distributed_realtime_bus
from app.realtime.hub import realtime_hub

app = FastAPI(title="Learning Intelligence Platform", version="0.1.0")

try:  # pragma: no cover
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
except Exception:  # pragma: no cover
    sentry_sdk = None  # type: ignore
    FastApiIntegration = None  # type: ignore

settings = get_settings()
if sentry_sdk is not None and FastApiIntegration is not None and settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

configure_tracing()
register_exception_handlers(app)
register_rate_limiter(app)
register_security_middleware(app)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(api_router)
app.include_router(metrics_router)


@app.on_event("startup")
async def startup_event() -> None:
    await distributed_realtime_bus.start(realtime_hub.handle_distributed_message)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await distributed_realtime_bus.close()


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "Learning Intelligence Platform API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health() -> dict:
    checks: dict[str, dict[str, str | bool]] = {}

    db_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
        checks["database"] = {"status": "ok"}
    except Exception as exc:
        checks["database"] = {"status": "error", "detail": type(exc).__name__}

    redis_ok = False
    redis_client = get_redis_client()
    if redis_client is None:
        checks["redis"] = {"status": "unavailable", "detail": "client_not_configured"}
    else:
        try:
            await redis_client.ping()
            redis_ok = True
            checks["redis"] = {"status": "ok"}
        except Exception as exc:
            checks["redis"] = {"status": "error", "detail": type(exc).__name__}

    celery_ok = False
    try:
        insp = celery_app.control.inspect(timeout=1.0)
        ping_result = insp.ping() if insp is not None else None
        celery_ok = bool(ping_result)
        checks["celery"] = {"status": "ok" if celery_ok else "degraded"}
    except CeleryError as exc:
        checks["celery"] = {"status": "error", "detail": type(exc).__name__}
    except Exception as exc:
        checks["celery"] = {"status": "error", "detail": type(exc).__name__}

    overall_ok = db_ok and redis_ok and celery_ok
    return {
        "status": "ok" if overall_ok else "degraded",
        "checks": checks,
    }
