"""fastapi-starlette-essentials — the production middleware you keep rewriting.

Core, always-available exports (need only ``fastapi``):

    from fastapi_starlette_essentials import (
        SecurityHeadersMiddleware,
        RequestLoggingMiddleware,
        register_error_handlers,
        PaginationParams,
        PaginatedResponse,
    )

Extra-gated components are imported from their submodules:

    from fastapi_starlette_essentials.auth import JWTManager, JWTConfig          # [jwt]
    from fastapi_starlette_essentials.cache import RedisCache                    # [redis]
    from fastapi_starlette_essentials.middleware.rate_limit import create_limiter  # [ratelimit]
    from fastapi_starlette_essentials.middleware.metrics import PrometheusMetricsMiddleware  # [metrics]
"""

from ._logging import LoggerLike
from .middleware import (
    DEFAULT_CSP,
    DEFAULT_PERMISSIONS_POLICY,
    SPA_DEV_CSP,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    register_error_handlers,
)
from .pagination import PaginatedResponse, PaginationParams

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "LoggerLike",
    "SecurityHeadersMiddleware",
    "RequestLoggingMiddleware",
    "register_error_handlers",
    "PaginationParams",
    "PaginatedResponse",
    "DEFAULT_CSP",
    "SPA_DEV_CSP",
    "DEFAULT_PERMISSIONS_POLICY",
]