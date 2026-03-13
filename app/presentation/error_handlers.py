from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.exceptions import (
    ApplicationError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


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
    async def handle_application_error(_: Request, exc: ApplicationError):
        return JSONResponse(
            status_code=application_error_status_code(exc),
            content={"detail": str(exc)},
        )
