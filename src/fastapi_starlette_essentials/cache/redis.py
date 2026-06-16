"""Async Redis cache with JSON serialization and graceful degradation.

The cache never raises on Redis errors: if Redis is unconfigured or
unreachable, reads return ``None``/``0``/``False`` and the app keeps working.
The Redis URL is passed explicitly; there is no global settings lookup.
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from .._logging import LoggerLike, resolve_logger


class RedisCache:
    """Async Redis cache client with JSON values and best-effort semantics.

    Example:
        >>> cache = RedisCache("redis://localhost:6379/0")
        >>> await cache.connect()           # doctest: +SKIP
        >>> await cache.set("k", {"a": 1})  # doctest: +SKIP
        >>> await cache.get("k")            # doctest: +SKIP
        {'a': 1}
    """

    def __init__(
        self,
        redis_url: str | None,
        *,
        logger: LoggerLike | None = None,
        max_connections: int = 10,
    ) -> None:
        self._redis_url = redis_url
        self._max_connections = max_connections
        self._log = resolve_logger(logger, __name__)
        self.redis: aioredis.Redis | None = None
        self.enabled = False

    async def connect(self) -> None:
        """Connect to Redis and verify with a ping. No-op if no URL configured."""
        if not self._redis_url:
            self._log.warning("redis url not configured; caching disabled")
            return
        try:
            self.redis = aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self._max_connections,
            )
            await self.redis.ping()
            self.enabled = True
            self._log.info("redis connected: %s", self._redis_url)
        except Exception as exc:  # noqa: BLE001 - best-effort cache
            self._log.error("redis connection failed: %s", exc, exc_info=True)
            self.redis = None
            self.enabled = False

    async def disconnect(self) -> None:
        """Close the Redis connection if open."""
        if self.redis:
            await self.redis.aclose()
            self._log.info("redis disconnected")

    async def get(self, key: str) -> Any | None:
        """Return the JSON-decoded value for ``key``, or ``None``."""
        if not self.enabled or not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            if value:
                self._log.debug("cache hit: %s", key)
                return json.loads(value)
            self._log.debug("cache miss: %s", key)
            return None
        except Exception as exc:  # noqa: BLE001
            self._log.error("cache get error key=%s: %s", key, exc)
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """JSON-encode and store ``value`` under ``key`` with a TTL (seconds)."""
        if not self.enabled or not self.redis:
            return False
        try:
            await self.redis.set(key, json.dumps(value), ex=ttl)
            self._log.debug("cache set: %s ttl=%s", key, ttl)
            return True
        except Exception as exc:  # noqa: BLE001
            self._log.error("cache set error key=%s: %s", key, exc)
            return False

    async def delete(self, key: str) -> bool:
        """Delete a single key. Returns ``True`` on success."""
        if not self.enabled or not self.redis:
            return False
        try:
            await self.redis.delete(key)
            self._log.debug("cache delete: %s", key)
            return True
        except Exception as exc:  # noqa: BLE001
            self._log.error("cache delete error key=%s: %s", key, exc)
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching ``pattern`` (e.g. ``"inspections:*"``). Returns count."""
        if not self.enabled or not self.redis:
            return 0
        try:
            keys = [key async for key in self.redis.scan_iter(match=pattern)]
            if keys:
                deleted = await self.redis.delete(*keys)
                self._log.debug("cache delete_pattern: %s count=%s", pattern, deleted)
                return int(deleted)
            return 0
        except Exception as exc:  # noqa: BLE001
            self._log.error("cache delete_pattern error pattern=%s: %s", pattern, exc)
            return 0

    async def clear(self) -> bool:
        """Flush the current Redis database. Returns ``True`` on success."""
        if not self.enabled or not self.redis:
            return False
        try:
            await self.redis.flushdb()
            self._log.info("cache cleared")
            return True
        except Exception as exc:  # noqa: BLE001
            self._log.error("cache clear error: %s", exc)
            return False