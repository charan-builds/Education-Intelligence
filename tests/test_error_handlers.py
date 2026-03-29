import asyncio
import json

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from app.application.exceptions import ApplicationError, ValidationError
from app.presentation.error_handlers import register_exception_handlers


def _request(path: str, headers: list[tuple[bytes, bytes]] | None = None) -> Request:
    async def _receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers or [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    return Request(scope, _receive)


def _decode_response(response) -> dict:
    return json.loads(response.body.decode())


def test_application_error_returns_structured_payload():
    async def _run():
        app = FastAPI()
        register_exception_handlers(app)
        request = _request("/application-error")
        request.state.request_id = "req-1"
        request.state.correlation_id = "corr-1"

        handler = app.exception_handlers[ApplicationError]
        response = await handler(request, ValidationError("bad payload"))

        assert response.status_code == 400
        body = _decode_response(response)
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"] == "bad payload"
        assert body["detail"] == "bad payload"
        assert body["request_id"] == "req-1"
        assert body["correlation_id"] == "corr-1"

    asyncio.run(_run())


def test_http_exception_returns_structured_payload():
    async def _run():
        app = FastAPI()
        register_exception_handlers(app)
        request = _request("/http-error")
        request.state.request_id = "req-2"
        request.state.correlation_id = "req-2"

        handler = app.exception_handlers[HTTPException]
        response = await handler(request, HTTPException(status_code=403, detail="Forbidden"))

        assert response.status_code == 403
        body = _decode_response(response)
        assert body["success"] is False
        assert body["error"] == "Forbidden"
        assert body["detail"] == "Forbidden"
        assert body["request_id"] == "req-2"
        assert body["correlation_id"] == "req-2"

    asyncio.run(_run())


def test_validation_error_returns_structured_payload():
    async def _run():
        app = FastAPI()
        register_exception_handlers(app)
        request = _request("/echo/not-an-int")

        handler = app.exception_handlers[RequestValidationError]
        response = await handler(
            request,
            RequestValidationError(
                [
                    {
                        "type": "int_parsing",
                        "loc": ("path", "value"),
                        "msg": "Input should be a valid integer, unable to parse string as an integer",
                        "input": "not-an-int",
                    }
                ]
            ),
        )

        assert response.status_code == 422
        body = _decode_response(response)
        assert body["success"] is False
        assert body["error"] == "Request validation failed"
        assert body["detail"] == "Request validation failed"
        assert body["validation_errors"]

    asyncio.run(_run())


def test_unhandled_exception_returns_internal_server_error_payload():
    async def _run():
        app = FastAPI()
        register_exception_handlers(app)
        request = _request("/crash")
        request.state.correlation_id = "corr-500"

        handler = app.exception_handlers[Exception]
        response = await handler(request, RuntimeError("boom"))

        assert response.status_code == 500
        body = _decode_response(response)
        assert body["success"] is False
        assert body["error"] == "Internal server error"
        assert body["detail"] == "Internal server error"
        assert body["correlation_id"] == "corr-500"

    asyncio.run(_run())
