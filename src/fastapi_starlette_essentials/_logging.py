"""Internal helper for the injectable-logger pattern.

Every component that logs accepts an optional ``logger``. When omitted, a
standard-library :class:`logging.Logger` is used. All log calls use %-style
message formatting (``logger.info("connected %s", url)``) so they work
identically with a stdlib logger or a structlog bound logger.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LoggerLike(Protocol):
    """Minimal logger interface accepted by this package."""

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> Any: ...
    def info(self, msg: str, *args: Any, **kwargs: Any) -> Any: ...
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> Any: ...
    def error(self, msg: str, *args: Any, **kwargs: Any) -> Any: ...


def resolve_logger(logger: LoggerLike | None, name: str) -> LoggerLike:
    """Return ``logger`` if provided, else a stdlib logger named ``name``."""
    return logger if logger is not None else logging.getLogger(name)