import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from fastapi_starlette_essentials import (
    DEFAULT_CSP,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    register_error_handlers,
)


def build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    register_error_handlers(app, show_details=False)

    @app.get("/ok")
    async def ok():
        return {"ok": True}

    @app.get("/boom")
    async def boom():
        raise RuntimeError("kaboom")

    @app.get("/forbidden")
    async def forbidden():
        raise HTTPException(status_code=403, detail="nope")

    @app.get("/needs-query")
    async def needs_query(q: int):  # missing/invalid q -> RequestValidationError
        return {"q": q}

    return app


def test_security_headers_present():
    client = TestClient(build_app())
    r = client.get("/ok")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Content-Security-Policy"] == DEFAULT_CSP
    # HSTS only on https
    assert "Strict-Transport-Security" not in r.headers


def test_hsts_on_https():
    client = TestClient(build_app(), base_url="https://testserver")
    r = client.get("/ok")
    assert "max-age=" in r.headers["Strict-Transport-Security"]


def test_request_id_header():
    client = TestClient(build_app())
    r = client.get("/ok")
    assert r.headers.get("X-Request-ID")


def test_http_exception_shape():
    client = TestClient(build_app())
    r = client.get("/forbidden")
    assert r.status_code == 403
    body = r.json()
    assert body["error_code"] == "FORBIDDEN"
    assert body["detail"] == "nope"


def test_validation_error_shape():
    client = TestClient(build_app())
    r = client.get("/needs-query?q=notanint")
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["errors"] and "field" in body["errors"][0]


def test_unhandled_exception_hidden():
    client = TestClient(build_app(), raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.status_code == 500
    body = r.json()
    assert body["error_code"] == "INTERNAL_ERROR"
    assert body["detail"] == "Internal server error"  # hidden because show_details=False


def test_unhandled_exception_shown_when_details_on():
    app = FastAPI()
    register_error_handlers(app, show_details=True)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("kaboom")

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.json()["detail"] == "kaboom"


@pytest.mark.parametrize("path,code", [("/ok", 200), ("/forbidden", 403)])
def test_endpoints_smoke(path, code):
    client = TestClient(build_app())
    assert client.get(path).status_code == code