"""Async Redis cache (requires the ``redis`` extra; see the README for install)."""

from .redis import RedisCache

__all__ = ["RedisCache"]