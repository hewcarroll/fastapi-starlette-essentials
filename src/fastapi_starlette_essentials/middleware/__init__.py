"""Middleware and error handlers.

The always-available pieces (security headers, error handlers, request logging)
are re-exported here. Rate limiting and Prometheus metrics require extras and
are imported from their submodules:

    from fastapi_starlette_essentials.middleware.rate_limit import create_limiter
    from fastapi_starlette_essentials.middleware.metrics import PrometheusMetricsMiddleware
"""

from .error_handlers import register_error_handlers
from .logging import RequestLoggingMiddleware
from .security_headers import (
    DEFAULT_CSP,
    DEFAULT_PERMISSIONS_POLICY,
    SPA_DEV_CSP,
    SecurityHeadersMiddleware,
)

__all__ = [
    "register_error_handlers",
    "RequestLoggingMiddleware",
    "SecurityHeadersMiddleware",
    "DEFAULT_CSP",
    "SPA_DEV_CSP",
    "DEFAULT_PERMISSIONS_POLICY",
]