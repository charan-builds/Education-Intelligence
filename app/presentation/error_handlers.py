from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.application.exceptions import (
    ApplicationError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.core.logging import get_logger


logger = get_logger()


def _error_payload(request: Request, message: str, *, code: str | None = None) -> dict[str, object]:
    request_id = getattr(request.state, "request_id", None)
    correlation_id = getattr(request.state, "correlation_id", request_id)
    payload: dict[str, object] = {
        "success": False,
        "data": None,
        "error": message,
        "detail": message,
    }
    if code is not None:
        payload["code"] = code
    if request_id is not None:
        payload["request_id"] = request_id
    if correlation_id is not None:
        payload["correlation_id"] = correlation_id
    return payload


def application_error_status_code(exc: ApplicationError) -> int:
    if isinstance(exc, NotFoundError):
        return 404
    if isinstance(exc, UnauthorizedError):
        return 401
    if isinstance(exc, ConflictError):
        return 409
    if isinstance(exc, ValidationError):
        return 400
    return 400


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def handle_application_error(request: Request, exc: ApplicationError):
        return JSONResponse(
            status_code=application_error_status_code(exc),
            content=_error_payload(request, str(exc), code=type(exc).__name__),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(request, detail, code="HTTPException"),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                **_error_payload(request, "Request validation failed", code="RequestValidationError"),
                "validation_errors": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception):
        logger.error(
            "unhandled exception",
            extra={
                "log_data": {
                    "request_id": getattr(request.state, "request_id", None),
                    "correlation_id": getattr(request.state, "correlation_id", None),
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            },
        )
        return JSONResponse(
            status_code=500,
            content=_error_payload(request, "Internal server error", code="InternalServerError"),
        )
