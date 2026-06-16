"""JWT helpers (requires the ``jwt`` extra: ``pip install fastapi-starlette-essentials[jwt]``)."""

from .jwt import JWTConfig, JWTManager

__all__ = ["JWTConfig", "JWTManager"]