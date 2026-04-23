from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.application import (
    ApplicationError,
    ConflictAppError,
    ForbiddenAppError,
    NotFoundAppError,
    UnauthorizedAppError,
    ValidationAppError,
)


def _status_from_error(exc: ApplicationError) -> int:
    if isinstance(exc, ValidationAppError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY
    if isinstance(exc, NotFoundAppError):
        return status.HTTP_404_NOT_FOUND
    if isinstance(exc, UnauthorizedAppError):
        return status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, ForbiddenAppError):
        return status.HTTP_403_FORBIDDEN
    if isinstance(exc, ConflictAppError):
        return status.HTTP_409_CONFLICT
    return status.HTTP_400_BAD_REQUEST


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def handle_application_error(
        _request: Request,
        exc: ApplicationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=_status_from_error(exc),
            content={"error": exc.__class__.__name__, "message": str(exc)},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "RequestValidationError",
                "message": "Invalid request payload",
                "details": exc.errors(),
            },
        )
