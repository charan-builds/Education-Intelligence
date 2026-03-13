from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings


class AuthenticationError(Exception):
    pass


class PasswordValidationError(Exception):
    pass


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: str | dict[str, Any], expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"exp": expire}
    if isinstance(subject, dict):
        payload.update(subject)
    else:
        payload["sub"] = subject
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp = payload.get("exp")
        if exp is None:
            raise AuthenticationError("Token missing expiration")
        exp_datetime = datetime.fromtimestamp(float(exp), tz=timezone.utc)
        if exp_datetime <= datetime.now(timezone.utc):
            raise AuthenticationError("Token expired")
        return payload
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired token") from exc


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
