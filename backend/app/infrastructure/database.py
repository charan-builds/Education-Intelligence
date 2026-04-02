from collections.abc import AsyncGenerator
import time

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.logging import get_logger
from app.core.metrics import db_query_duration_seconds, db_slow_queries_total
from app.core.config import get_settings

settings = get_settings()
logger = get_logger()

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
AsyncSessionLocal = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


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


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
