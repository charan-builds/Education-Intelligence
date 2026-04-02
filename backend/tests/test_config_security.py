import pytest

from app.core.config import Settings


def test_settings_accepts_jwt_secret_alias():
    settings = Settings(
        database_url="postgresql+asyncpg://postgres:postgres@postgres:5432/learning_platform",
        secret_key="x" * 40,
    )
    assert settings.secret_key == "x" * 40


def test_settings_rejects_weak_secret_in_production():
    with pytest.raises(ValueError, match="JWT_SECRET/SECRET_KEY must be a strong production secret"):
        Settings(
            database_url="postgresql+asyncpg://postgres:postgres@postgres:5432/learning_platform",
            secret_key="supersecret",
            environment="production",
            auth_cookie_secure=True,
        )


def test_settings_rejects_insecure_cookies_in_production():
    with pytest.raises(ValueError, match="AUTH_COOKIE_SECURE must be true in production"):
        Settings(
            database_url="postgresql+asyncpg://postgres:postgres@postgres:5432/learning_platform",
            secret_key="x" * 40,
            environment="production",
            auth_cookie_secure=False,
        )
