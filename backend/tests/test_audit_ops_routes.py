import asyncio
from datetime import datetime, timezone
import hashlib
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.presentation import audit_routes


class _FakeAuditLogService:
    last_args = None

    def list_feature_flag_events(self, *, tenant_id, limit, offset, since, until, feature_name, order):
        _FakeAuditLogService.last_args = {
            "tenant_id": tenant_id,
            "limit": limit,
            "offset": offset,
            "since": since,
            "until": until,
            "feature_name": feature_name,
            "order": order,
        }
        return [{"event": "feature_flag_updated"}]

    def export_feature_flag_events_csv(self, *, tenant_id, limit, offset, since, until, feature_name, order):
        _FakeAuditLogService.last_args = {
            "tenant_id": tenant_id,
            "limit": limit,
            "offset": offset,
            "since": since,
            "until": until,
            "feature_name": feature_name,
            "order": order,
        }
        return "timestamp,feature_name\n2026-03-12T10:00:00+00:00,ml_recommendation_enabled\n", False

    def list_feature_names(self, *, tenant_id, since, until):
        _FakeAuditLogService.last_args = {
            "tenant_id": tenant_id,
            "since": since,
            "until": until,
        }
        return ["adaptive_testing_enabled", "ml_recommendation_enabled"]


def _user(role: str, tenant_id: int = 10):
    return SimpleNamespace(role=SimpleNamespace(value=role), tenant_id=tenant_id)


def _request():
    return SimpleNamespace(state=SimpleNamespace(user=None), client=SimpleNamespace(host="127.0.0.1"), headers={})


def test_audit_logs_forbidden_for_student(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await audit_routes.list_feature_flag_audit_logs(
                request=_request(),
                tenant_id=None,
                limit=50,
                offset=0,
                since=None,
                until=None,
                feature_name=None,
                order="desc",
                current_user=_user("student", tenant_id=5),
            )
        assert exc.value.status_code == 403

    asyncio.run(_run())


def test_audit_logs_admin_scoped_to_current_tenant(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        since = datetime(2026, 3, 12, 10, 0, tzinfo=timezone.utc)
        until = datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc)
        result = await audit_routes.list_feature_flag_audit_logs(
            request=_request(),
            tenant_id=99,
            limit=10,
            offset=3,
            since=since,
            until=until,
            feature_name="ml_recommendation_enabled",
            order="asc",
            current_user=_user("admin", tenant_id=7),
        )
        payload = result.body.decode()
        assert '"event":"feature_flag_updated"' in payload
        assert '"limit":10' in payload
        assert '"offset":3' in payload
        assert '"returned":1' in payload
        assert '"has_more":false' in payload
        assert '"next_offset":null' in payload
        assert _FakeAuditLogService.last_args == {
            "tenant_id": 7,
            "limit": 11,
            "offset": 3,
            "since": since,
            "until": until,
            "feature_name": "ml_recommendation_enabled",
            "order": "asc",
        }

    asyncio.run(_run())


def test_audit_logs_super_admin_can_scope_tenant(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        await audit_routes.list_feature_flag_audit_logs(
            request=_request(),
            tenant_id=22,
            limit=12,
            offset=0,
            since=None,
            until=None,
            feature_name=None,
            order="desc",
            current_user=_user("super_admin", tenant_id=1),
        )
        assert _FakeAuditLogService.last_args == {
            "tenant_id": 22,
            "limit": 13,
            "offset": 0,
            "since": None,
            "until": None,
            "feature_name": None,
            "order": "desc",
        }

    asyncio.run(_run())


def test_export_audit_logs_csv(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        result = await audit_routes.export_feature_flag_audit_logs(
            request=_request(),
            tenant_id=22,
            limit=12,
            offset=0,
            since=None,
            until=None,
            feature_name=None,
            order="desc",
            current_user=_user("super_admin", tenant_id=1),
        )
        assert result.media_type == "text/csv"
        body = result.body.decode()
        assert "feature_name" in body
        assert result.headers["X-Export-Row-Count"] == "1"
        assert result.headers["X-Export-SHA256"] == hashlib.sha256(body.encode("utf-8")).hexdigest()
        assert result.headers["X-Export-Has-More"] == "false"
        assert result.headers["X-Export-Next-Offset"] == ""
        assert result.headers["Cache-Control"] == "private, max-age=30"
        assert result.headers["Vary"] == "Authorization, If-None-Match"
        assert _FakeAuditLogService.last_args["tenant_id"] == 22

    asyncio.run(_run())


def test_audit_list_etag_304(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        first = await audit_routes.list_feature_flag_audit_logs(
            request=_request(),
            tenant_id=22,
            limit=12,
            offset=0,
            since=None,
            until=None,
            feature_name=None,
            order="desc",
            current_user=_user("super_admin", tenant_id=1),
        )
        etag = first.headers.get("etag")
        req = _request()
        req.headers = {"if-none-match": etag}
        second = await audit_routes.list_feature_flag_audit_logs(
            request=req,
            tenant_id=22,
            limit=12,
            offset=0,
            since=None,
            until=None,
            feature_name=None,
            current_user=_user("super_admin", tenant_id=1),
        )
        assert second.status_code == 304
        assert second.headers["Cache-Control"] == "private, max-age=30"
        assert second.headers["Vary"] == "Authorization, If-None-Match"

    asyncio.run(_run())


def test_audit_export_etag_304(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        first = await audit_routes.export_feature_flag_audit_logs(
            request=_request(),
            tenant_id=22,
            limit=12,
            offset=0,
            since=None,
            until=None,
            feature_name=None,
            current_user=_user("super_admin", tenant_id=1),
        )
        etag = first.headers.get("etag")
        req = _request()
        req.headers = {"if-none-match": etag}
        second = await audit_routes.export_feature_flag_audit_logs(
            request=req,
            tenant_id=22,
            limit=12,
            offset=0,
            since=None,
            until=None,
            feature_name=None,
            current_user=_user("super_admin", tenant_id=1),
        )
        assert second.status_code == 304
        assert second.headers["Cache-Control"] == "private, max-age=30"
        assert second.headers["Vary"] == "Authorization, If-None-Match"

    asyncio.run(_run())


def test_audit_list_invalid_time_range(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await audit_routes.list_feature_flag_audit_logs(
                request=_request(),
                tenant_id=22,
                limit=12,
                offset=0,
                since=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
                until=datetime(2026, 3, 12, 10, 0, tzinfo=timezone.utc),
                feature_name=None,
                order="desc",
                current_user=_user("super_admin", tenant_id=1),
            )
        assert exc.value.status_code == 400

    asyncio.run(_run())


def test_audit_export_invalid_time_range(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await audit_routes.export_feature_flag_audit_logs(
                request=_request(),
                tenant_id=22,
                limit=12,
                offset=0,
                since=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
                until=datetime(2026, 3, 12, 10, 0, tzinfo=timezone.utc),
                feature_name=None,
                order="desc",
                current_user=_user("super_admin", tenant_id=1),
            )
        assert exc.value.status_code == 400

    asyncio.run(_run())


def test_audit_list_lookback_too_large(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await audit_routes.list_feature_flag_audit_logs(
                request=_request(),
                tenant_id=22,
                limit=12,
                offset=0,
                since=datetime(2000, 1, 1, tzinfo=timezone.utc),
                until=None,
                feature_name=None,
                order="desc",
                current_user=_user("super_admin", tenant_id=1),
            )
        assert exc.value.status_code == 400

    asyncio.run(_run())


def test_audit_export_lookback_too_large(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await audit_routes.export_feature_flag_audit_logs(
                request=_request(),
                tenant_id=22,
                limit=12,
                offset=0,
                since=datetime(2000, 1, 1, tzinfo=timezone.utc),
                until=None,
                feature_name=None,
                order="desc",
                current_user=_user("super_admin", tenant_id=1),
            )
        assert exc.value.status_code == 400

    asyncio.run(_run())


def test_audit_feature_names_admin(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        since = datetime(2026, 3, 12, 8, 0, tzinfo=timezone.utc)
        until = datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc)
        result = await audit_routes.list_feature_flag_audit_names(
            request=_request(),
            tenant_id=999,
            since=since,
            until=until,
            current_user=_user("admin", tenant_id=7),
        )
        payload = result.body.decode()
        assert "adaptive_testing_enabled" in payload
        assert "ml_recommendation_enabled" in payload
        assert result.headers["Cache-Control"] == "private, max-age=30"
        assert result.headers["Vary"] == "Authorization, If-None-Match"
        assert _FakeAuditLogService.last_args == {"tenant_id": 7, "since": since, "until": until}

    asyncio.run(_run())


def test_audit_feature_names_etag_304(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        first = await audit_routes.list_feature_flag_audit_names(
            request=_request(),
            tenant_id=22,
            since=None,
            until=None,
            current_user=_user("super_admin", tenant_id=1),
        )
        etag = first.headers.get("etag")
        req = _request()
        req.headers = {"if-none-match": etag}
        second = await audit_routes.list_feature_flag_audit_names(
            request=req,
            tenant_id=22,
            since=None,
            until=None,
            current_user=_user("super_admin", tenant_id=1),
        )
        assert second.status_code == 304
        assert second.headers["Cache-Control"] == "private, max-age=30"
        assert second.headers["Vary"] == "Authorization, If-None-Match"

    asyncio.run(_run())


def test_audit_feature_names_invalid_time_range(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await audit_routes.list_feature_flag_audit_names(
                request=_request(),
                tenant_id=22,
                since=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
                until=datetime(2026, 3, 12, 10, 0, tzinfo=timezone.utc),
                current_user=_user("super_admin", tenant_id=1),
            )
        assert exc.value.status_code == 400

    asyncio.run(_run())


def test_audit_feature_names_lookback_too_large(monkeypatch):
    monkeypatch.setattr(audit_routes, "AuditLogService", lambda: _FakeAuditLogService())

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await audit_routes.list_feature_flag_audit_names(
                request=_request(),
                tenant_id=22,
                since=datetime(2000, 1, 1, tzinfo=timezone.utc),
                until=None,
                current_user=_user("super_admin", tenant_id=1),
            )
        assert exc.value.status_code == 400

    asyncio.run(_run())
