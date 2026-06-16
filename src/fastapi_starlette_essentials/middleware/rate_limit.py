"""Rate-limiting helpers built on slowapi (requires the ``ratelimit`` extra).

slowapi attaches limits via decorators bound to a :class:`~slowapi.Limiter`.
This module gives you a limiter factory, a proxy-aware client-IP helper, and an
optional set of sensible named presets. Wire the limiter into your app per the
slowapi docs (add the ``SlowAPIMiddleware`` and the 429 exception handler).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from slowapi import Limiter
from slowapi.util import get_remote_address

if TYPE_CHECKING:
    from starlette.requests import Request


def get_client_ip(request: "Request") -> str:
    """Return the client IP, honoring the first ``X-Forwarded-For`` entry."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def create_limiter(key_func: Callable[..., str] = get_remote_address, **kwargs: object) -> Limiter:
    """Create a slowapi :class:`Limiter`. Pass ``key_func=get_client_ip`` behind a proxy."""
    return Limiter(key_func=key_func, **kwargs)


def common_limiters(limiter: Limiter) -> dict[str, Callable]:
    """Return a dict of example named limit decorators bound to ``limiter``.

    Apply them to routes, e.g. ``@limiters["login"]``. Tune to taste.
    """
    return {
        "login": limiter.limit("5/15minute"),
        "register": limiter.limit("3/hour"),
        "password_reset": limiter.limit("3/hour"),
        "refresh": limiter.limit("20/minute"),
        "api": limiter.limit("100/minute"),
        "write": limiter.limit("30/minute"),
        "report": limiter.limit("10/minute"),
    }