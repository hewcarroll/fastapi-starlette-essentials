"""Request-logging middleware: assigns a request ID, times the request, and
logs start/finish. The request ID is stored on ``request.state.request_id`` and
echoed back in the ``X-Request-ID`` response header.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .._logging import LoggerLike, resolve_logger

if TYPE_CHECKING:
    from starlette.types import ASGIApp


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with a generated request ID and timing."""

    def __init__(self, app: "ASGIApp", *, logger: LoggerLike | None = None) -> None:
        super().__init__(app)
        self._log = resolve_logger(logger, __name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        client_host = request.client.host if request.client else None
        start_time = time.perf_counter()

        self._log.info(
            "incoming request id=%s %s %s client=%s",
            request_id,
            request.method,
            request.url.path,
            client_host,
        )

        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001 - re-raised after logging
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log.error(
                "request failed id=%s %s %s after %.2fms: %s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
                exc,
                exc_info=True,
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000
        self._log.info(
            "request completed id=%s %s %s -> %s in %.2fms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response