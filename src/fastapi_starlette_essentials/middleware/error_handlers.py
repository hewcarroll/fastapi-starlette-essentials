"""Global exception handlers for consistent JSON API error responses.

Registers handlers for request-validation errors (422 with field detail),
``HTTPException`` (standardised body with a machine-readable ``error_code``),
and any unhandled exception (500). Whether the 500 body reveals the real error
message is controlled by ``show_details`` — there is no global settings lookup.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from .._logging import LoggerLike, resolve_logger

# Map common HTTP status codes to machine-readable error code strings.
_STATUS_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    429: "RATE_LIMITED",
}


def register_error_handlers(
    app: FastAPI,
    *,
    show_details: bool = False,
    logger: LoggerLike | None = None,
) -> None:
    """Register the standard exception handlers on ``app``.

    Args:
        app: the FastAPI application.
        show_details: if True, the 500 response body contains the real
            exception message (use in development; keep False in production).
        logger: optional logger; defaults to a stdlib logger.
    """
    log = resolve_logger(logger, __name__)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors: list[dict[str, str]] = []
        for err in exc.errors():
            loc_parts = [str(p) for p in err.get("loc", [])]
            field = ".".join(loc_parts[1:]) if len(loc_parts) > 1 else ".".join(loc_parts)
            errors.append({"field": field, "message": err.get("msg", "Invalid value")})
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "errors": errors,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail or "An error occurred",
                "error_code": _STATUS_CODE_MAP.get(exc.status_code, "ERROR"),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        log.error(
            "unhandled exception on %s %s",
            request.method,
            request.url.path,
            exc_info=True,
        )
        detail = str(exc) if show_details else "Internal server error"
        return JSONResponse(
            status_code=500,
            content={"detail": detail, "error_code": "INTERNAL_ERROR"},
        )