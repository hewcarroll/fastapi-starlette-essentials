# fastapi-starlette-essentials

The production middleware you keep rewriting for every FastAPI/Starlette service —
security headers, consistent JSON error handling, request logging with request IDs,
pagination, JWT, an async Redis cache, rate limiting, and Prometheus metrics —
extracted into one small, **dependency-light** package with **no global settings
coupling** and an **injectable logger**.

Each component takes explicit configuration; nothing reaches into a global
`get_settings()`. Where a component logs, it accepts an optional `logger` and
defaults to the standard library (log calls use `%`-formatting, so a `structlog`
bound logger works too).

## Install

The package isn't on PyPI; install it from this repository. The core
(security headers, error handlers, request logging, pagination) needs only
`fastapi`. The rest are opt-in extras:

```sh
REPO=git+https://github.com/hewcarroll/fastapi-starlette-essentials
pip install "$REPO"                                          # core
pip install "fastapi-starlette-essentials[jwt] @ $REPO"      # + JWT
pip install "fastapi-starlette-essentials[redis] @ $REPO"    # + async Redis cache
pip install "fastapi-starlette-essentials[ratelimit] @ $REPO"  # + slowapi helpers
pip install "fastapi-starlette-essentials[metrics] @ $REPO"    # + Prometheus
pip install "fastapi-starlette-essentials[all] @ $REPO"        # everything
```

## Quick start

```python
from fastapi import FastAPI
from fastapi_starlette_essentials import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    register_error_handlers,
    PaginatedResponse,
    PaginationParams,
)

app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)          # strict CSP by default
app.add_middleware(RequestLoggingMiddleware)           # X-Request-ID + timing
register_error_handlers(app, show_details=False)       # consistent JSON errors
```

### Security headers

Strict, same-origin CSP by default. Override per app, or use the bundled
SPA-development policy:

```python
from fastapi_starlette_essentials import SecurityHeadersMiddleware, SPA_DEV_CSP

app.add_middleware(SecurityHeadersMiddleware, csp=SPA_DEV_CSP)   # local React/Vite
app.add_middleware(SecurityHeadersMiddleware, hsts=False)        # behind TLS-terminating proxy
```

### Error handlers

`register_error_handlers(app, show_details=...)` installs handlers that return a
consistent body — `{"detail": ..., "error_code": ...}` — for validation errors
(422 with field-level detail), `HTTPException`, and unhandled exceptions (500,
message hidden unless `show_details=True`).

### Pagination

```python
from fastapi_starlette_essentials import PaginationParams, PaginatedResponse

@app.get("/items")
async def list_items(params: PaginationParams = Depends()):
    rows = db.query(...).offset(params.offset).limit(params.limit).all()
    total = db.query(...).count()
    return PaginatedResponse.create(items=rows, total=total, params=params)
```

### JWT  `[jwt]`

```python
from fastapi_starlette_essentials.auth import JWTManager, JWTConfig

jwt = JWTManager(JWTConfig(secret=SECRET, access_token_expire_minutes=30))
token = jwt.create_access_token({"sub": user_id})
payload = jwt.verify_token(token)        # None if invalid/expired/wrong-type
```

### Async Redis cache  `[redis]`

Best-effort: if Redis is unconfigured or unreachable, reads return `None` and the
app keeps serving.

```python
from fastapi_starlette_essentials.cache import RedisCache

cache = RedisCache(REDIS_URL, logger=my_logger)
await cache.connect()
await cache.set("user:1", {"name": "hew"}, ttl=60)
await cache.get("user:1")                # {'name': 'hew'}
```

### Rate limiting  `[ratelimit]`

```python
from fastapi_starlette_essentials.middleware.rate_limit import create_limiter, get_client_ip, common_limiters

limiter = create_limiter(key_func=get_client_ip)   # proxy-aware
limiters = common_limiters(limiter)                # {"login": ..., "api": ..., ...}

@app.post("/login")
@limiters["login"]
async def login(...): ...
```

Wire `limiter` into your app per the [slowapi docs](https://slowapi.readthedocs.io/)
(add `SlowAPIMiddleware` and the 429 handler).

### Prometheus metrics  `[metrics]`

```python
from prometheus_client import make_asgi_app
from fastapi_starlette_essentials.middleware.metrics import PrometheusMetricsMiddleware

app.add_middleware(PrometheusMetricsMiddleware)
app.mount("/metrics", make_asgi_app())
```

## Development

```sh
pip install -e ".[dev]"
pytest
```

## License

Dual-licensed under [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE) at your option.