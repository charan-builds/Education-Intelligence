import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.presentation import feature_flag_routes


class _DummySession:
    pass


class _FakeFeatureFlagService:
    last_tenant_id = None
    last_enable_args = None
    last_disable_args = None

    def __init__(self, session):
        self.session = session

    async def list_for_tenant(self, tenant_id: int):
        _FakeFeatureFlagService.last_tenant_id = tenant_id
        return [
            SimpleNamespace(
                id=1,
                tenant_id=tenant_id,
                feature_name="ml_recommendation_enabled",
                enabled=True,
                created_at=datetime.now(timezone.utc),
            )
        ]

    async def is_enabled(self, flag_name: str, tenant_id: int):
        return False

    async def enable_feature(self, flag_name: str, tenant_id: int):
        _FakeFeatureFlagService.last_enable_args = {"flag_name": flag_name, "tenant_id": tenant_id}
        return SimpleNamespace(
            id=2,
            tenant_id=tenant_id,
            feature_name=flag_name,
            enabled=True,
            created_at=datetime.now(timezone.utc),
        )

    async def disable_feature(self, flag_name: str, tenant_id: int):
        _FakeFeatureFlagService.last_disable_args = {"flag_name": flag_name, "tenant_id": tenant_id}
        return SimpleNamespace(
            id=3,
            tenant_id=tenant_id,
            feature_name=flag_name,
            enabled=False,
            created_at=datetime.now(timezone.utc),
        )


def _user(role: str, tenant_id: int = 10):
    return SimpleNamespace(role=SimpleNamespace(value=role), tenant_id=tenant_id)


def test_feature_flags_forbidden_for_student(monkeypatch):
    monkeypatch.setattr(feature_flag_routes, "FeatureFlagService", _FakeFeatureFlagService)

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await feature_flag_routes.list_feature_flags(
                tenant_id=None,
                db=_DummySession(),
                current_user=_user("student", tenant_id=5),
            )
        assert exc.value.status_code == 403

    asyncio.run(_run())


def test_feature_flags_admin_scoped_tenant(monkeypatch):
    monkeypatch.setattr(feature_flag_routes, "FeatureFlagService", _FakeFeatureFlagService)

    async def _run():
        result = await feature_flag_routes.list_feature_flags(
            tenant_id=999,
            db=_DummySession(),
            current_user=_user("admin", tenant_id=42),
        )
        assert _FakeFeatureFlagService.last_tenant_id == 42
        assert len(result.items) == 1
        assert result.items[0].tenant_id == 42

    asyncio.run(_run())


def test_feature_flags_super_admin_explicit_tenant(monkeypatch):
    monkeypatch.setattr(feature_flag_routes, "FeatureFlagService", _FakeFeatureFlagService)

    async def _run():
        result = await feature_flag_routes.list_feature_flags(
            tenant_id=77,
            db=_DummySession(),
            current_user=_user("super_admin", tenant_id=1),
        )
        assert _FakeFeatureFlagService.last_tenant_id == 77
        assert result.items[0].tenant_id == 77

    asyncio.run(_run())


def test_update_feature_flag_admin_scoped(monkeypatch):
    from app.schemas.feature_flag_schema import FeatureFlagUpdateRequest

    monkeypatch.setattr(feature_flag_routes, "FeatureFlagService", _FakeFeatureFlagService)

    async def _run():
        result = await feature_flag_routes.update_feature_flag(
            flag_name="ml_recommendation_enabled",
            payload=FeatureFlagUpdateRequest(enabled=True, tenant_id=999),
            db=_DummySession(),
            current_user=_user("admin", tenant_id=12),
        )
        assert result.enabled is True
        assert _FakeFeatureFlagService.last_enable_args == {
            "flag_name": "ml_recommendation_enabled",
            "tenant_id": 12,
        }

    asyncio.run(_run())


def test_update_feature_flag_super_admin_tenant_override(monkeypatch):
    from app.schemas.feature_flag_schema import FeatureFlagUpdateRequest

    monkeypatch.setattr(feature_flag_routes, "FeatureFlagService", _FakeFeatureFlagService)

    async def _run():
        result = await feature_flag_routes.update_feature_flag(
            flag_name="adaptive_testing_enabled",
            payload=FeatureFlagUpdateRequest(enabled=False, tenant_id=55),
            db=_DummySession(),
            current_user=_user("super_admin", tenant_id=1),
        )
        assert result.enabled is False
        assert _FakeFeatureFlagService.last_disable_args == {
            "flag_name": "adaptive_testing_enabled",
            "tenant_id": 55,
        }

    asyncio.run(_run())


def test_feature_flag_catalog_admin(monkeypatch):
    async def _run():
        result = await feature_flag_routes.feature_flag_catalog(
            current_user=_user("admin", tenant_id=12),
        )
        assert "adaptive_testing_enabled" in result.items
        assert "ai_mentor_enabled" in result.items
        assert "ml_recommendation_enabled" in result.items
        assert result.items == sorted(result.items)

    asyncio.run(_run())


def test_update_feature_flag_rejects_unknown_flag(monkeypatch):
    from app.schemas.feature_flag_schema import FeatureFlagUpdateRequest

    monkeypatch.setattr(feature_flag_routes, "FeatureFlagService", _FakeFeatureFlagService)

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await feature_flag_routes.update_feature_flag(
                flag_name="unknown_flag",
                payload=FeatureFlagUpdateRequest(enabled=True, tenant_id=999),
                db=_DummySession(),
                current_user=_user("admin", tenant_id=12),
            )
        assert exc.value.status_code == 400

    asyncio.run(_run())
