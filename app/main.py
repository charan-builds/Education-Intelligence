from fastapi import FastAPI

from app.core.metrics import metrics_router
from app.core.security_middleware import register_security_middleware
from app.presentation.api_router import api_router
from app.presentation.error_handlers import register_exception_handlers
from app.presentation.middleware.logging_middleware import RequestLoggingMiddleware
from app.presentation.middleware.rate_limiter import register_rate_limiter

app = FastAPI(title="Learning Intelligence Platform", version="0.1.0")
register_exception_handlers(app)
register_rate_limiter(app)
register_security_middleware(app)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(api_router)
app.include_router(metrics_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
