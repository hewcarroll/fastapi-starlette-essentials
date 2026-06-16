from datetime import timedelta

import pytest

from fastapi_starlette_essentials.auth import JWTConfig, JWTManager


@pytest.fixture
def mgr() -> JWTManager:
    return JWTManager(JWTConfig(secret="test-secret"))


def test_empty_secret_rejected():
    with pytest.raises(ValueError):
        JWTManager(JWTConfig(secret=""))


def test_roundtrip_access_token(mgr: JWTManager):
    token = mgr.create_access_token({"sub": "user-123"})
    payload = mgr.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert "jti" in payload


def test_refresh_type_is_enforced(mgr: JWTManager):
    refresh = mgr.create_refresh_token({"sub": "u"})
    # Verifying a refresh token as an access token must fail.
    assert mgr.verify_token(refresh, token_type="access") is None
    assert mgr.verify_token(refresh, token_type="refresh") is not None


def test_expired_token_rejected(mgr: JWTManager):
    token = mgr.create_access_token({"sub": "u"}, expires_delta=timedelta(seconds=-1))
    assert mgr.verify_token(token) is None


def test_wrong_secret_rejected(mgr: JWTManager):
    token = mgr.create_access_token({"sub": "u"})
    other = JWTManager(JWTConfig(secret="different"))
    assert other.verify_token(token) is None


def test_decode_unsafe_skips_signature(mgr: JWTManager):
    token = mgr.create_access_token({"sub": "u"})
    other = JWTManager(JWTConfig(secret="different"))
    # Signature verification would fail with the wrong secret...
    assert other.verify_token(token) is None
    # ...but the unsafe decode skips the signature and still returns the payload.
    assert other.decode_token_unsafe(token)["sub"] == "u"