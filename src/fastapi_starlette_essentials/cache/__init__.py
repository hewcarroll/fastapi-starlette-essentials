"""Async Redis cache (requires the ``redis`` extra: ``pip install fastapi-starlette-essentials[redis]``)."""

from .redis import RedisCache

__all__ = ["RedisCache"]