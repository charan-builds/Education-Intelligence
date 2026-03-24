import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.core.metrics import error_count, request_duration, total_requests


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger()

    @staticmethod
    def _extract_context(request: Request) -> tuple[int | None, int | None]:
        user = getattr(request.state, "user", None)
        if user is None:
            return None, None

        tenant_id = getattr(user, "tenant_id", None)
        user_id = getattr(user, "id", None)
        return tenant_id, user_id

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        request_id = str(uuid4())
        request.state.request_id = request_id

        tenant_id, user_id = self._extract_context(request)

        try:
            response: Response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000)
            endpoint = request.url.path
            method = request.method
            status_code = str(response.status_code)

            total_requests.labels(endpoint=endpoint, method=method, status_code=status_code).inc()
            request_duration.labels(endpoint=endpoint, method=method, status_code=status_code).observe(
                duration_ms / 1000
            )

            self.logger.info(
                "request completed",
                extra={
                    "log_data": {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "tenant_id": tenant_id,
                        "actor_tenant_id": getattr(request.state, "actor_tenant_id", tenant_id),
                        "user_id": user_id,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    }
                },
            )
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000)
            endpoint = request.url.path
            method = request.method
            status_code = "500"
            total_requests.labels(endpoint=endpoint, method=method, status_code=status_code).inc()
            request_duration.labels(endpoint=endpoint, method=method, status_code=status_code).observe(
                duration_ms / 1000
            )
            error_count.labels(endpoint=endpoint, method=method, status_code=status_code).inc()
            self.logger.error(
                "request failed",
                extra={
                    "log_data": {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "tenant_id": tenant_id,
                        "actor_tenant_id": getattr(request.state, "actor_tenant_id", tenant_id),
                        "user_id": user_id,
                        "status_code": 500,
                        "duration_ms": duration_ms,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    }
                },
            )
            raise
