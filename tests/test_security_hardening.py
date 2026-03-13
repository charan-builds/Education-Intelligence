import pytest

from app.core.security import AuthenticationError, PasswordValidationError, decode_access_token, validate_password_strength
from app.core.config import get_settings
from jose import jwt


def test_password_strength_validation_rejects_weak_password():
    with pytest.raises(PasswordValidationError):
        validate_password_strength("short")


def test_password_strength_validation_accepts_alnum_password():
    validate_password_strength("secure123")


def test_decode_access_token_rejects_missing_exp():
    settings = get_settings()
    token = jwt.encode({"sub": "1"}, settings.secret_key, algorithm=settings.algorithm)
    with pytest.raises(AuthenticationError):
        decode_access_token(token)
