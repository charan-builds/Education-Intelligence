import pytest

from app.core.security import (
    AuthenticationError,
    create_access_token,
    create_refresh_token_with_jti,
    decode_access_token,
    decode_refresh_token,
    enforce_roles,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    password = "strong-password"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_jwt_round_trip():
    token = create_access_token({"sub": "12", "tenant_id": 3, "role": "student"})
    payload = decode_access_token(token)
    assert payload["sub"] == "12"
    assert payload["tenant_id"] == 3
    assert payload["role"] == "student"


def test_enforce_roles_requires_explicit_mentor_membership():
    enforce_roles("mentor", {"mentor", "admin"})

    with pytest.raises(AuthenticationError):
        enforce_roles("mentor", {"teacher"})


def test_refresh_token_round_trip_with_jti():
    token = create_refresh_token_with_jti(
        {"sub": "12", "tenant_id": 3, "role": "student"},
        token_id="session-123",
    )
    payload = decode_refresh_token(token)
    assert payload["jti"] == "session-123"
