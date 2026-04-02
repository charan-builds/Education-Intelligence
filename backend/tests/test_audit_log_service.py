from pathlib import Path
from datetime import datetime, timezone, timedelta

from app.application.services.audit_log_service import AuditLogService


def test_list_feature_flag_events_filters_and_limits(tmp_path: Path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "\n".join(
            [
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"a"}',
                '{"event":"other_event","target_tenant_id":2}',
                '{"event":"feature_flag_updated","target_tenant_id":3,"feature_name":"b"}',
                'not-json',
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"c"}',
            ]
        ),
        encoding="utf-8",
    )

    service = AuditLogService(log_file_path=str(log_file))
    items = service.list_feature_flag_events(tenant_id=2, limit=2)

    assert len(items) == 2
    assert items[0]["feature_name"] == "c"
    assert items[1]["feature_name"] == "a"


def test_list_feature_flag_events_offset(tmp_path: Path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "\n".join(
            [
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"a"}',
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"b"}',
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"c"}',
            ]
        ),
        encoding="utf-8",
    )
    service = AuditLogService(log_file_path=str(log_file))
    items = service.list_feature_flag_events(tenant_id=2, limit=1, offset=1)
    assert len(items) == 1
    assert items[0]["feature_name"] == "b"


def test_list_feature_flag_events_since_until(tmp_path: Path):
    base = datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc)
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "\n".join(
            [
                f'{{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"a","timestamp":"{(base - timedelta(hours=2)).isoformat()}"}}',
                f'{{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"b","timestamp":"{base.isoformat()}"}}',
                f'{{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"c","timestamp":"{(base + timedelta(hours=2)).isoformat()}"}}',
            ]
        ),
        encoding="utf-8",
    )
    service = AuditLogService(log_file_path=str(log_file))
    items = service.list_feature_flag_events(
        tenant_id=2,
        limit=10,
        since=base - timedelta(minutes=30),
        until=base + timedelta(minutes=30),
    )
    assert len(items) == 1
    assert items[0]["feature_name"] == "b"


def test_list_feature_flag_events_feature_name_filter(tmp_path: Path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "\n".join(
            [
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"ml_recommendation_enabled"}',
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"adaptive_testing_enabled"}',
            ]
        ),
        encoding="utf-8",
    )
    service = AuditLogService(log_file_path=str(log_file))
    items = service.list_feature_flag_events(
        tenant_id=2,
        limit=10,
        feature_name="adaptive_testing_enabled",
    )
    assert len(items) == 1
    assert items[0]["feature_name"] == "adaptive_testing_enabled"


def test_list_feature_flag_events_order_asc(tmp_path: Path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "\n".join(
            [
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"first"}',
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"second"}',
            ]
        ),
        encoding="utf-8",
    )
    service = AuditLogService(log_file_path=str(log_file))
    items = service.list_feature_flag_events(tenant_id=2, limit=10, order="asc")
    assert len(items) == 2
    assert items[0]["feature_name"] == "first"
    assert items[1]["feature_name"] == "second"


def test_list_feature_names_unique_sorted(tmp_path: Path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "\n".join(
            [
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"b"}',
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"a"}',
                '{"event":"feature_flag_updated","target_tenant_id":2,"feature_name":"b"}',
            ]
        ),
        encoding="utf-8",
    )
    service = AuditLogService(log_file_path=str(log_file))
    names = service.list_feature_names(tenant_id=2)
    assert names == ["a", "b"]


def test_list_feature_flag_events_missing_file_returns_empty(tmp_path: Path):
    service = AuditLogService(log_file_path=str(tmp_path / "missing.log"))
    assert service.list_feature_flag_events(tenant_id=None, limit=50) == []


def test_export_feature_flag_events_csv(tmp_path: Path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        '{"event":"feature_flag_updated","timestamp":"2026-03-12T10:00:00+00:00","actor_user_id":1,'
        '"actor_role":"admin","target_tenant_id":2,"feature_name":"ml_recommendation_enabled",'
        '"previous_enabled":false,"new_enabled":true,"path":"/ops/feature-flags/{flag_name}","method":"POST"}',
        encoding="utf-8",
    )
    service = AuditLogService(log_file_path=str(log_file))
    csv_text, has_more = service.export_feature_flag_events_csv(tenant_id=2, limit=10)
    assert "feature_name" in csv_text
    assert "ml_recommendation_enabled" in csv_text
    assert has_more is False
