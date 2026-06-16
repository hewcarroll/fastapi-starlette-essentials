"""Security-headers middleware for Starlette/FastAPI apps.

Adds CSP, HSTS (HTTPS only), X-Content-Type-Options, X-Frame-Options,
Referrer-Policy and Permissions-Policy. The CSP and Permissions-Policy are
configurable; the defaults are strict. A relaxed, SPA-friendly CSP is provided
as :data:`SPA_DEV_CSP` for local React/Vite development.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.types import ASGIApp

# Strict default: same-origin only, no framing, no plugins.
DEFAULT_CSP = "; ".join(
    [
        "default-src 'self'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "object-src 'none'",
        "img-src 'self' data:",
        "upgrade-insecure-requests",
    ]
)

# Relaxed policy for local SPA development (inline scripts/styles, localhost API).
SPA_DEV_CSP = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "font-src 'self' data:",
        "connect-src 'self' http://localhost:* https:",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "upgrade-insecure-requests",
    ]
)

DEFAULT_PERMISSIONS_POLICY = ", ".join(
    [
        "geolocation=()",
        "microphone=()",
        "camera=()",
        "payment=()",
        "usb=()",
        "magnetometer=()",
        "gyroscope=()",
        "accelerometer=()",
    ]
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach security headers to every response.

    Args:
        app: the ASGI app.
        csp: Content-Security-Policy value (default: :data:`DEFAULT_CSP`).
            Pass ``None`` to omit the CSP header entirely.
        permissions_policy: Permissions-Policy value
            (default: :data:`DEFAULT_PERMISSIONS_POLICY`; ``None`` to omit).
        hsts: send Strict-Transport-Security on HTTPS requests (default True).
        hsts_max_age: HSTS max-age in seconds (default 1 year).
        hsts_preload: add ``preload`` to the HSTS header (default True).
        referrer_policy: Referrer-Policy value.
        remove_server_header: strip the ``Server`` header (default True).
    """

    def __init__(
        self,
        app: "ASGIApp",
        *,
        csp: str | None = DEFAULT_CSP,
        permissions_policy: str | None = DEFAULT_PERMISSIONS_POLICY,
        hsts: bool = True,
        hsts_max_age: int = 31_536_000,
        hsts_preload: bool = True,
        referrer_policy: str = "strict-origin-when-cross-origin",
        remove_server_header: bool = True,
    ) -> None:
        super().__init__(app)
        self.csp = csp
        self.permissions_policy = permissions_policy
        self.hsts = hsts
        self.hsts_max_age = hsts_max_age
        self.hsts_preload = hsts_preload
        self.referrer_policy = referrer_policy
        self.remove_server_header = remove_server_header

    async def dispatch(self, request: "Request", call_next: Any) -> "Response":
        response = await call_next(request)

        if self.csp is not None:
            response.headers["Content-Security-Policy"] = self.csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = self.referrer_policy
        if self.permissions_policy is not None:
            response.headers["Permissions-Policy"] = self.permissions_policy

        if self.hsts and request.url.scheme == "https":
            value = f"max-age={self.hsts_max_age}; includeSubDomains"
            if self.hsts_preload:
                value += "; preload"
            response.headers["Strict-Transport-Security"] = value

        if self.remove_server_header and "server" in response.headers:
            del response.headers["server"]

        return response