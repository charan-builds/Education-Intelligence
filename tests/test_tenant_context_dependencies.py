import asyncio
from types import SimpleNamespace

from starlette.requests import Request

from app.core.dependencies import get_current_user


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

    request = _request(headers=[(b"x-tenant-id", b"9")])
    user = asyncio.run(get_current_user(request=request, token="token", db=object()))

    assert user.tenant_id == 5
    assert request.state.actor_tenant_id == 5
    assert request.state.tenant_id == 5
