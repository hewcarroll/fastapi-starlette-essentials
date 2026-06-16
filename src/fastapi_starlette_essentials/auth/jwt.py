"""JWT access/refresh token creation and verification.

Configuration is explicit (a :class:`JWTConfig`); there is no global settings
lookup. Construct one :class:`JWTManager` at startup and reuse it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt


@dataclass(frozen=True)
class JWTConfig:
    """Signing configuration for :class:`JWTManager`."""

    secret: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


class JWTManager:
    """Create and verify signed JWT access/refresh tokens.

    Example:
        >>> mgr = JWTManager(JWTConfig(secret="change-me"))
        >>> token = mgr.create_access_token({"sub": "user-123"})
        >>> mgr.verify_token(token)["sub"]
        'user-123'
    """

    def __init__(self, config: JWTConfig) -> None:
        if not config.secret:
            raise ValueError("JWTConfig.secret must be a non-empty string")
        self._cfg = config

    def create_access_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a signed access token. ``data`` is typically ``{"sub": user_id}``."""
        to_encode = data.copy()
        expire = datetime.now(UTC) + (
            expires_delta
            if expires_delta is not None
            else timedelta(minutes=self._cfg.access_token_expire_minutes)
        )
        to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
        return jwt.encode(to_encode, self._cfg.secret, algorithm=self._cfg.algorithm)

    def create_refresh_token(self, data: dict[str, Any]) -> str:
        """Create a longer-lived signed refresh token."""
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=self._cfg.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
        return jwt.encode(to_encode, self._cfg.secret, algorithm=self._cfg.algorithm)

    def verify_token(
        self,
        token: str,
        token_type: str = "access",
    ) -> dict[str, Any] | None:
        """Verify a token's signature/expiry and type. Returns the payload or ``None``."""
        try:
            payload = jwt.decode(token, self._cfg.secret, algorithms=[self._cfg.algorithm])
        except JWTError:
            return None
        if payload.get("type") != token_type:
            return None
        return payload

    def decode_token_unsafe(self, token: str) -> dict[str, Any] | None:
        """Decode WITHOUT verifying the signature. For debugging only — never auth."""
        try:
            return jwt.decode(
                token,
                self._cfg.secret,
                algorithms=[self._cfg.algorithm],
                options={"verify_signature": False},
            )
        except JWTError:
            return None