import asyncio
from types import SimpleNamespace

from starlette.requests import Request

import pytest

from fastapi import HTTPException
from app.application.exceptions import UnauthorizedError
from app.core.dependencies import get_current_user, require_tenant_membership


def _request(headers: list[tuple[bytes, bytes]] | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": headers or [],
        }
    )


def test_super_admin_can_override_effective_tenant(monkeypatch):
    async def fake_get_by_id_in_tenant(self, user_id: int, tenant_id: int):
        assert user_id == 1
        assert tenant_id == 1
        return SimpleNamespace(id=1, tenant_id=1, role=SimpleNamespace(value="super_admin"))

    monkeypatch.setattr(
        "app.core.dependencies.decode_access_token",
        lambda token: {"sub": "1", "tenant_id": 1, "role": "super_admin"},
    )
    monkeypatch.setattr(
        "app.core.dependencies.UserRepository.get_by_id_in_tenant",
        fake_get_by_id_in_tenant,
    )
    async def fake_get_membership(self, user_id, tenant_id):
        return None

    monkeypatch.setattr(
        "app.core.dependencies.UserTenantRoleRepository.get_membership",
        fake_get_membership,
    )

    request = _request(headers=[(b"x-tenant-id", b"3")])
    user = asyncio.run(get_current_user(request=request, token="token", db=object()))

    assert user.tenant_id == 3
    assert request.state.actor_tenant_id == 1
    assert request.state.tenant_id == 3


def test_non_super_admin_cannot_override_effective_tenant(monkeypatch):
    async def fake_get_by_id_in_tenant(self, user_id: int, tenant_id: int):
        assert user_id == 2
        assert tenant_id == 5
        return SimpleNamespace(id=2, tenant_id=5, role=SimpleNamespace(value="admin"))

    monkeypatch.setattr(
        "app.core.dependencies.decode_access_token",
        lambda token: {"sub": "2", "tenant_id": 5, "role": "admin"},
    )
    monkeypatch.setattr(
        "app.core.dependencies.UserRepository.get_by_id_in_tenant",
        fake_get_by_id_in_tenant,
    )
    async def fake_get_membership(self, user_id, tenant_id):
        return None

    monkeypatch.setattr(
        "app.core.dependencies.UserTenantRoleRepository.get_membership",
        fake_get_membership,
    )

    request = _request(headers=[(b"x-tenant-id", b"9")])
    with pytest.raises(HTTPException):
        asyncio.run(get_current_user(request=request, token="token", db=object()))


def test_require_tenant_membership_passes_with_valid_membership(monkeypatch):
    async def fake_validate_tenant_membership(user_id: int, tenant_id: int, db_session):
        assert user_id == 2
        assert tenant_id == 2
        return None

    user = SimpleNamespace(id=2, tenant_id=2)

    monkeypatch.setattr("app.core.dependencies.validate_tenant_membership", fake_validate_tenant_membership)

    result = asyncio.run(require_tenant_membership(current_user=user, db=object()))
    assert result is user


def test_require_tenant_membership_raises_without_membership(monkeypatch):
    async def fake_validate_tenant_membership(user_id: int, tenant_id: int, db_session):
        raise UnauthorizedError("User is not a member of the specified tenant")

    user = SimpleNamespace(id=3, tenant_id=3)

    monkeypatch.setattr("app.core.dependencies.validate_tenant_membership", fake_validate_tenant_membership)

    with pytest.raises(UnauthorizedError):
        asyncio.run(require_tenant_membership(current_user=user, db=object()))
