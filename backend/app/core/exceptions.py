import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.infrastructure.observability.request_context import current_request_id

logger = logging.getLogger(__name__)

_HTTP_CODES = {
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
}


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers or {}


def error_payload(request_id: str, code: str, message: str) -> dict[str, object]:
    return {"request_id": request_id, "error": {"code": code, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(current_request_id(request), exc.code, exc.message),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=error_payload(
                current_request_id(request),
                "INVALID_REQUEST",
                "La solicitud no es válida.",
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, "HTTP_ERROR")
        if isinstance(exc.detail, str):
            message = exc.detail
        else:
            message = "No se pudo completar la solicitud."
        headers = {}
        if exc.headers:
            headers.update({str(key): value for key, value in exc.headers.items()})
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(current_request_id(request), code, message),
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error", extra={"request_id": current_request_id(request)})
        return JSONResponse(
            status_code=500,
            content=error_payload(
                current_request_id(request),
                "INTERNAL_ERROR",
                "Ocurrió un error interno.",
            ),
        )
