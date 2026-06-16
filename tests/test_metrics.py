from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import generate_latest

from fastapi_starlette_essentials.middleware.metrics import PrometheusMetricsMiddleware


def test_metrics_recorded():
    app = FastAPI()
    app.add_middleware(PrometheusMetricsMiddleware)

    @app.get("/ping")
    async def ping():
        return {"pong": True}

    client = TestClient(app)
    assert client.get("/ping").status_code == 200

    exported = generate_latest().decode()
    assert "http_requests_total" in exported
    assert "http_request_duration_seconds" in exported