import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Request
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.logging import get_logger
from app.core.metrics import (
    db_query_duration_seconds,
    db_slow_queries_total,
    super_admin_sessions_active,
    super_admin_sessions_total,
)
from app.core.config import get_settings
from app.infrastructure.tenant_rls import apply_request_rls_context, apply_rls_context

settings = get_settings()
logger = get_logger()


class MissingTenantContextError(RuntimeError):
    pass


class TenantAwareAsyncSession(AsyncSession):
    def _ensure_tenant_context(self) -> None:
        if not bool(self.info.get("tenant_context_explicit")):
            raise MissingTenantContextError("Database session opened without explicit tenant context")
        if self.info.get("tenant_id") is None:
            raise MissingTenantContextError("Database session missing tenant_id")
        if not self.info.get("tenant_role"):
            raise MissingTenantContextError("Database session missing tenant role")

    async def execute(self, *args, **kwargs):
        self._ensure_tenant_context()
        return await super().execute(*args, **kwargs)

    async def scalar(self, *args, **kwargs):
        self._ensure_tenant_context()
        return await super().scalar(*args, **kwargs)

    async def scalars(self, *args, **kwargs):
        self._ensure_tenant_context()
        return await super().scalars(*args, **kwargs)

    async def get(self, *args, **kwargs):
        self._ensure_tenant_context()
        return await super().get(*args, **kwargs)

    async def stream(self, *args, **kwargs):
        self._ensure_tenant_context()
        return await super().stream(*args, **kwargs)

    async def flush(self, *args, **kwargs):
        self._ensure_tenant_context()
        return await super().flush(*args, **kwargs)

    async def commit(self) -> None:
        self._ensure_tenant_context()
        await super().commit()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout_seconds,
    pool_recycle=settings.database_pool_recycle_seconds,
    pool_use_lifo=settings.database_pool_use_lifo,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=TenantAwareAsyncSession)

ALLOWED_SUPER_ADMIN_SESSION_REASONS = frozenset(
    {
        "health_check",
        "open_system_session_alias",
        "mark_outbox_processed_without_tenant",
        "mark_outbox_failed_without_tenant",
        "list_student_tenant_ids",
        "process_outbox_events",
        "cleanup_outbox_events",
        "refresh_outbox_metrics",
        "recover_stuck_outbox_events",
        "refresh_platform_overview",
        "consume_kafka_events",
        "replay_kafka_topic",
    }
)


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # pragma: no cover
    conn.info.setdefault("query_start_time", []).append(time.perf_counter())


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # pragma: no cover
    start_time = conn.info.get("query_start_time", []).pop(-1)
    duration = max(time.perf_counter() - start_time, 0.0)
    operation = statement.split(None, 1)[0].lower() if statement else "unknown"
    db_query_duration_seconds.labels(operation=operation).observe(duration)
    if duration * 1000 >= settings.db_slow_query_threshold_ms:
        db_slow_queries_total.labels(operation=operation).inc()
        logger.warning(
            "slow query detected",
            extra={
                "log_data": {
                    "operation": operation,
                    "duration_ms": round(duration * 1000, 2),
                    "statement_preview": statement[:300] if statement else "",
                }
            },
        )


async def get_db_session(request: Request = None) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        await apply_request_rls_context(session, request)
        yield session


@asynccontextmanager
async def open_tenant_session(
    *,
    tenant_id: int,
    role: str,
    actor_user_id: int | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    if tenant_id is None or int(tenant_id) <= 0:
        raise MissingTenantContextError("tenant_id is required for tenant-scoped sessions")
    async with AsyncSessionLocal() as session:
        await apply_rls_context(session, tenant_id=int(tenant_id), role=role, actor_user_id=actor_user_id)
        yield session


@asynccontextmanager
async def open_super_admin_session(*, reason: str = "unspecified") -> AsyncGenerator[AsyncSession, None]:
    normalized_reason = (reason or "unspecified").strip()
    if normalized_reason not in ALLOWED_SUPER_ADMIN_SESSION_REASONS:
        raise ValueError(
            f"Unsupported super admin session reason: {normalized_reason}. "
            "Add the reason to ALLOWED_SUPER_ADMIN_SESSION_REASONS after review."
        )
    async with AsyncSessionLocal() as session:
        await apply_rls_context(
            session,
            tenant_id=int(settings.default_tenant_id),
            role="super_admin",
            actor_user_id=None,
        )
        session.info["super_admin_reason"] = normalized_reason
        super_admin_sessions_total.labels(reason=normalized_reason).inc()
        super_admin_sessions_active.labels(reason=normalized_reason).inc()
        logger.warning(
            "super_admin_session_opened",
            extra={"log_data": {"reason": normalized_reason}},
        )
        try:
            yield session
        finally:
            super_admin_sessions_active.labels(reason=normalized_reason).inc(-1.0)


@asynccontextmanager
async def open_system_session() -> AsyncGenerator[AsyncSession, None]:
    # Backward-compatible alias. Prefer open_super_admin_session() so RLS bypass
    # is explicit at the callsite and easier to audit.
    async with open_super_admin_session(reason="open_system_session_alias") as session:
        yield session
