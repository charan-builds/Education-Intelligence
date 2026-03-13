import asyncio

from starlette.requests import Request
from starlette.responses import Response

from app.presentation.middleware.logging_middleware import RequestLoggingMiddleware


class _DummyApp:
    async def __call__(self, scope, receive, send):
        return None


class _CaptureLogger:
    def __init__(self):
        self.info_calls = []
        self.error_calls = []

    def info(self, message, **kwargs):
        self.info_calls.append((message, kwargs))

    def error(self, message, **kwargs):
        self.error_calls.append((message, kwargs))


def _request(path: str = "/diagnostic/submit", method: str = "POST") -> Request:
    async def _receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    return Request(scope, _receive)


def test_middleware_logs_success_request():
    async def _run():
        middleware = RequestLoggingMiddleware(_DummyApp())
        logger = _CaptureLogger()
        middleware.logger = logger

        request = _request()

        async def call_next(_request_obj):
            return Response(status_code=200)

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 200
        assert len(logger.info_calls) == 1

        message, kwargs = logger.info_calls[0]
        data = kwargs["extra"]["log_data"]
        assert message == "request completed"
        assert data["method"] == "POST"
        assert data["path"] == "/diagnostic/submit"
        assert data["status_code"] == 200
        assert data["tenant_id"] is None
        assert data["user_id"] is None
        assert isinstance(data["duration_ms"], int)
        assert data["request_id"]

    asyncio.run(_run())


def test_middleware_logs_error_request():
    async def _run():
        middleware = RequestLoggingMiddleware(_DummyApp())
        logger = _CaptureLogger()
        middleware.logger = logger

        request = _request(path="/roadmap/12", method="GET")

        async def call_next(_request_obj):
            raise ValueError("boom")

        try:
            await middleware.dispatch(request, call_next)
            assert False, "Expected ValueError"
        except ValueError:
            pass

        assert len(logger.error_calls) == 1
        message, kwargs = logger.error_calls[0]
        data = kwargs["extra"]["log_data"]

        assert message == "request failed"
        assert data["method"] == "GET"
        assert data["path"] == "/roadmap/12"
        assert data["status_code"] == 500
        assert data["error_type"] == "ValueError"
        assert data["error_message"] == "boom"
        assert data["tenant_id"] is None
        assert data["user_id"] is None
        assert data["request_id"]

    asyncio.run(_run())
