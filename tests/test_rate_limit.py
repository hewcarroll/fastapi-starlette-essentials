from slowapi import Limiter
from starlette.requests import Request

from fastapi_starlette_essentials.middleware.rate_limit import (
    common_limiters,
    create_limiter,
    get_client_ip,
)


def _request(headers=None, client=("1.2.3.4", 0)) -> Request:
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request({"type": "http", "headers": raw_headers, "client": client})


def test_forwarded_for_takes_first_ip():
    req = _request({"X-Forwarded-For": "9.9.9.9, 8.8.8.8"})
    assert get_client_ip(req) == "9.9.9.9"


def test_falls_back_to_client_host():
    assert get_client_ip(_request()) == "1.2.3.4"


def test_unknown_when_no_client():
    assert get_client_ip(_request(client=None)) == "unknown"


def test_create_and_named_limiters():
    limiter = create_limiter()
    assert isinstance(limiter, Limiter)
    presets = common_limiters(limiter)
    assert {"login", "register", "api"} <= set(presets)