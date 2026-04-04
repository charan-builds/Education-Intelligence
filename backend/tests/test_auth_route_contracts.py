from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import Response
from starlette.requests import Request

from app.presentation import auth_routes
from app.application.services.auth_service import LoginResult
from app.schemas.auth_schema import LoginRequest


class _FakeAuthService:
    def __init__(self, session):
        self.session = session

    async def login(self, email, password, **kwargs):
        _ = password, kwargs
        user = SimpleNamespace(
            id=99,
            email=email,
            tenant_id=2,
            role="student",
            created_at=datetime.now(timezone.utc),
            is_email_verified=True,
            is_profile_completed=True,
            email_verified_at=None,
        )
        return LoginResult(
            access_token="access-token",
            refresh_token="refresh-token",
            user=user,
            effective_role="student",
            requires_profile_completion=False,
            scope="full_access",
        )


async def test_login_route_returns_token_response(monkeypatch):
    monkeypatch.setattr(auth_routes, "AuthService", _FakeAuthService)
    monkeypatch.setattr(auth_routes, "decode_access_token", lambda token: {"tenant_id": 2})

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/auth/login",
            "headers": [(b"host", b"demo.local"), (b"user-agent", b"pytest")],
        }
    )
    response = Response()

    result = await auth_routes.login(
        request=request,
        response=response,
        payload=LoginRequest(email="maya.chen@demo.learnova.ai", password="Student123!", tenant_id=2),
        db=SimpleNamespace(),
    )

    assert result.authenticated is True
    assert result.access_token == "access-token"
    assert result.user.tenant_id == 2
    assert "access_token=" in response.headers.get("set-cookie", "")
