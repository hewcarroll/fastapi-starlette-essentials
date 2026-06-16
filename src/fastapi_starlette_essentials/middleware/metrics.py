"""Prometheus metrics middleware (requires the ``metrics`` extra).

Records request count, duration, and request/response sizes. Metrics are
registered on the default Prometheus registry; expose them with
``prometheus_client.make_asgi_app()`` mounted at ``/metrics``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from starlette.types import ASGIApp

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)
REQUEST_SIZE = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
)
RESPONSE_SIZE = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Collect Prometheus metrics for each request."""

    def __init__(self, app: "ASGIApp") -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        method = request.method
        endpoint = request.url.path

        with REQUEST_DURATION.labels(method=method, endpoint=endpoint).time():
            response = await call_next(request)

        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=response.status_code).inc()

        if "content-length" in request.headers:
            try:
                REQUEST_SIZE.labels(method=method, endpoint=endpoint).observe(
                    int(request.headers["content-length"])
                )
            except (ValueError, TypeError):
                pass

        if "content-length" in response.headers:
            try:
                RESPONSE_SIZE.labels(method=method, endpoint=endpoint).observe(
                    int(response.headers["content-length"])
                )
            except (ValueError, TypeError):
                pass

        return response