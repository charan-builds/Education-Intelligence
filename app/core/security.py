from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from hashlib import sha1
import base64
import hmac
import struct
from uuid import uuid4
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings


class AuthenticationError(Exception):
    pass


class PasswordValidationError(Exception):
    pass


ACCESS_TOKEN_COOKIE_NAME = "access_token"
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_INVITE = "invite"
TOKEN_TYPE_EMAIL_VERIFICATION = "email_verification"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def _create_token(
    subject: str | dict[str, Any],
    *,
    token_type: str,
    expires_delta: timedelta,
    token_id: str | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    payload: dict[str, Any] = {
        "exp": expire,
        "iat": now,
        "type": token_type,
    }
    if token_id:
        payload["jti"] = token_id
    if isinstance(subject, dict):
        payload.update(subject)
    else:
        payload["sub"] = subject
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(
    subject: str | dict[str, Any],
    expires_delta: timedelta | None = None,
    *,
    token_id: str | None = None,
) -> str:
    settings = get_settings()
    return _create_token(
        subject,
        token_type=TOKEN_TYPE_ACCESS,
        expires_delta=expires_delta or timedelta(minutes=settings.access_token_expire_minutes),
        token_id=token_id,
    )


def create_refresh_token(subject: str | dict[str, Any], expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    return _create_token(
        subject,
        token_type=TOKEN_TYPE_REFRESH,
        expires_delta=expires_delta or timedelta(minutes=settings.refresh_token_expire_minutes),
        token_id=uuid4().hex,
    )


def create_refresh_token_with_jti(
    subject: str | dict[str, Any],
    *,
    token_id: str,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    return _create_token(
        subject,
        token_type=TOKEN_TYPE_REFRESH,
        expires_delta=expires_delta or timedelta(minutes=settings.refresh_token_expire_minutes),
        token_id=token_id,
    )


def create_invite_token(
    *,
    tenant_id: int,
    role: str,
    email: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    payload: dict[str, Any] = {"tenant_id": tenant_id, "role": role}
    if email is not None:
        payload["email"] = email
    return _create_token(
        payload,
        token_type=TOKEN_TYPE_INVITE,
        expires_delta=expires_delta or timedelta(hours=settings.invite_token_expire_hours),
    )


def create_email_verification_token(
    *,
    user_id: int,
    tenant_id: int,
    email: str,
    expires_delta: timedelta | None = None,
) -> str:
    return _create_token(
        {"sub": str(user_id), "tenant_id": tenant_id, "email": email},
        token_type=TOKEN_TYPE_EMAIL_VERIFICATION,
        expires_delta=expires_delta or timedelta(hours=24),
    )


def create_password_reset_token(
    *,
    user_id: int,
    tenant_id: int,
    email: str,
    expires_delta: timedelta | None = None,
) -> str:
    return _create_token(
        {"sub": str(user_id), "tenant_id": tenant_id, "email": email},
        token_type=TOKEN_TYPE_PASSWORD_RESET,
        expires_delta=expires_delta or timedelta(hours=2),
    )


def _parse_expiration(exp: Any) -> datetime:
    if isinstance(exp, datetime):
        return exp.astimezone(timezone.utc)
    return datetime.fromtimestamp(float(exp), tz=timezone.utc)


def decode_token(token: str, *, expected_type: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp = payload.get("exp")
        if exp is None:
            raise AuthenticationError("Token missing expiration")
        exp_datetime = _parse_expiration(exp)
        if exp_datetime <= datetime.now(timezone.utc):
            raise AuthenticationError("Token expired")
        token_type = payload.get("type")
        if expected_type is not None and token_type != expected_type:
            raise AuthenticationError("Invalid token type")
        return payload
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired token") from exc


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type=TOKEN_TYPE_ACCESS)


def decode_refresh_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type=TOKEN_TYPE_REFRESH)


def decode_invite_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type=TOKEN_TYPE_INVITE)


def decode_email_verification_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type=TOKEN_TYPE_EMAIL_VERIFICATION)


def decode_password_reset_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type=TOKEN_TYPE_PASSWORD_RESET)


def get_token_from_headers_and_cookies(
    headers: Mapping[str, str],
    cookies: Mapping[str, str],
    *,
    cookie_name: str = ACCESS_TOKEN_COOKIE_NAME,
) -> str | None:
    auth_header = headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            return token
    cookie_token = cookies.get(cookie_name)
    if cookie_token:
        return cookie_token
    return None


def enforce_roles(user_role: str, allowed_roles: set[str]) -> None:
    if user_role not in allowed_roles:
        raise AuthenticationError("Insufficient permissions")


def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise PasswordValidationError("Password must be at least 8 characters long")
    if not any(ch.isalpha() for ch in password):
        raise PasswordValidationError("Password must contain at least one letter")
    if not any(ch.isdigit() for ch in password):
        raise PasswordValidationError("Password must contain at least one number")


def generate_totp_secret(length: int = 32) -> str:
    raw = base64.b32encode(uuid4().bytes + uuid4().bytes).decode("ascii").rstrip("=")
    return raw[:length]


def build_totp_uri(*, secret: str, account_name: str, issuer: str) -> str:
    normalized_account = account_name.replace(" ", "%20")
    normalized_issuer = issuer.replace(" ", "%20")
    return f"otpauth://totp/{normalized_issuer}:{normalized_account}?secret={secret}&issuer={normalized_issuer}&digits=6&period=30"


def _totp_counter(for_time: datetime | None = None, period_seconds: int = 30) -> int:
    current = for_time or datetime.now(timezone.utc)
    return int(current.timestamp()) // period_seconds


def generate_totp_code(secret: str, *, for_time: datetime | None = None, period_seconds: int = 30) -> str:
    normalized_secret = secret.strip().replace(" ", "").upper()
    padding = "=" * ((8 - len(normalized_secret) % 8) % 8)
    key = base64.b32decode(f"{normalized_secret}{padding}")
    counter = _totp_counter(for_time=for_time, period_seconds=period_seconds)
    digest = hmac.new(key, struct.pack(">Q", counter), sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code_int % 1_000_000).zfill(6)


def verify_totp_code(
    secret: str,
    code: str,
    *,
    at_time: datetime | None = None,
    period_seconds: int = 30,
    allowed_drift_steps: int = 1,
) -> bool:
    normalized_code = "".join(ch for ch in code if ch.isdigit())
    if len(normalized_code) != 6:
        return False
    reference_time = at_time or datetime.now(timezone.utc)
    for offset in range(-allowed_drift_steps, allowed_drift_steps + 1):
        candidate_time = reference_time + timedelta(seconds=offset * period_seconds)
        if hmac.compare_digest(generate_totp_code(secret, for_time=candidate_time, period_seconds=period_seconds), normalized_code):
            return True
    return False
