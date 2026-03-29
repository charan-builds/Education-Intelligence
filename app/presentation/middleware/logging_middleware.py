import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.core.metrics import error_count, request_duration, requests_in_flight, total_requests
from app.core.tracing import get_tracer


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger()
        self.tracer = get_tracer("app.request")

    @staticmethod
    def _extract_context(request: Request) -> tuple[int | None, int | None]:
        user = getattr(request.state, "user", None)
        if user is None:
            return None, None

        # Prefer scalar auth-context fields first so logging never triggers lazy ORM refreshes
        # while handling request failures.
        tenant_id = getattr(user, "effective_tenant_id", None)
        if tenant_id is None:
            try:
                tenant_id = getattr(user, "tenant_id", None)
            except Exception:
                tenant_id = None

        user_id = getattr(user, "actor_user_id", None)
        if user_id is None:
            try:
                user_id = getattr(user, "id", None)
            except Exception:
                user_id = None
        return tenant_id, user_id

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        correlation_id = request.headers.get("X-Correlation-ID") or request_id
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        tenant_id, user_id = self._extract_context(request)
        requests_in_flight.labels(method=request.method).inc()

        try:
            if self.tracer is not None:
                with self.tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
                    span.set_attribute("http.method", request.method)
                    span.set_attribute("http.path", request.url.path)
                    span.set_attribute("http.route", getattr(request.scope.get("route"), "path", request.url.path))
                    span.set_attribute("request.id", request_id)
                    span.set_attribute("correlation.id", correlation_id)
                    if tenant_id is not None:
                        span.set_attribute("tenant.id", int(tenant_id))
                    if user_id is not None:
                        span.set_attribute("user.id", int(user_id))
                    response = await call_next(request)
            else:
                response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000)
            endpoint = getattr(getattr(request.scope.get("route"), "path", None), "strip", lambda: request.url.path)()
            method = request.method
            status_code = str(response.status_code)
            tenant_id, user_id = self._extract_context(request)

            total_requests.labels(endpoint=endpoint, method=method, status_code=status_code).inc()
            request_duration.labels(endpoint=endpoint, method=method, status_code=status_code).observe(
                duration_ms / 1000
            )

            self.logger.info(
                "request completed",
                extra={
                    "log_data": {
                        "request_id": request_id,
                        "correlation_id": correlation_id,
                        "route": endpoint,
                        "method": request.method,
                        "path": request.url.path,
                        "query": request.url.query or None,
                        "tenant_id": tenant_id,
                        "actor_tenant_id": getattr(request.state, "actor_tenant_id", tenant_id),
                        "user_id": user_id,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "client_ip": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent"),
                    }
                },
            )
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000)
            endpoint = getattr(getattr(request.scope.get("route"), "path", None), "strip", lambda: request.url.path)()
            method = request.method
            status_code = "500"
            tenant_id, user_id = self._extract_context(request)
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
                        "correlation_id": correlation_id,
                        "route": endpoint,
                        "method": request.method,
                        "path": request.url.path,
                        "query": request.url.query or None,
                        "tenant_id": tenant_id,
                        "actor_tenant_id": getattr(request.state, "actor_tenant_id", tenant_id),
                        "user_id": user_id,
                        "status_code": 500,
                        "duration_ms": duration_ms,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        "client_ip": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent"),
                    }
                },
            )
            raise
        finally:
            requests_in_flight.labels(method=request.method).dec()
