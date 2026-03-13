from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.core.config import get_settings


class AuditLogService:
    def __init__(self, log_file_path: str | None = None):
        settings = get_settings()
        self.log_file_path = log_file_path or settings.audit_log_file_path

    def list_feature_flag_events(
        self,
        *,
        tenant_id: int | None,
        limit: int = 100,
        offset: int = 0,
        since: datetime | None = None,
        until: datetime | None = None,
        feature_name: str | None = None,
        order: str = "desc",
    ) -> list[dict]:
        if not self.log_file_path:
            return []

        path = Path(self.log_file_path)
        if not path.exists() or not path.is_file():
            return []

        events: list[dict] = []
        seen = 0
        try:
            with path.open("r", encoding="utf-8") as fp:
                lines = fp.readlines()
                sequence = reversed(lines) if order == "desc" else lines
                for raw_line in sequence:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(record, dict):
                        continue
                    if record.get("event") != "feature_flag_updated":
                        continue
                    if tenant_id is not None and int(record.get("target_tenant_id", -1)) != int(tenant_id):
                        continue
                    if feature_name is not None and str(record.get("feature_name")) != feature_name:
                        continue
                    ts_raw = record.get("timestamp")
                    if isinstance(ts_raw, str):
                        try:
                            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                        except ValueError:
                            ts = None
                    else:
                        ts = None
                    if since is not None and ts is not None and ts < since:
                        continue
                    if until is not None and ts is not None and ts > until:
                        continue
                    if seen < offset:
                        seen += 1
                        continue
                    events.append(record)
                    if len(events) >= limit:
                        break
        except OSError:
            return []

        return events

    def export_feature_flag_events_csv(
        self,
        *,
        tenant_id: int | None,
        limit: int = 1000,
        offset: int = 0,
        since: datetime | None = None,
        until: datetime | None = None,
        feature_name: str | None = None,
        order: str = "desc",
    ) -> tuple[str, bool]:
        import csv
        import io

        raw_items = self.list_feature_flag_events(
            tenant_id=tenant_id,
            limit=limit + 1,
            offset=offset,
            since=since,
            until=until,
            feature_name=feature_name,
            order=order,
        )
        has_more = len(raw_items) > limit
        items = raw_items[:limit]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "timestamp",
                "actor_user_id",
                "actor_role",
                "target_tenant_id",
                "feature_name",
                "previous_enabled",
                "new_enabled",
                "path",
                "method",
            ]
        )
        for item in items:
            writer.writerow(
                [
                    item.get("timestamp"),
                    item.get("actor_user_id"),
                    item.get("actor_role"),
                    item.get("target_tenant_id"),
                    item.get("feature_name"),
                    item.get("previous_enabled"),
                    item.get("new_enabled"),
                    item.get("path"),
                    item.get("method"),
                ]
            )
        return output.getvalue(), has_more

    def list_feature_names(
        self,
        *,
        tenant_id: int | None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[str]:
        items = self.list_feature_flag_events(
            tenant_id=tenant_id,
            limit=10_000,
            offset=0,
            since=since,
            until=until,
            feature_name=None,
            order="desc",
        )
        names = sorted({str(item.get("feature_name")) for item in items if item.get("feature_name")})
        return names
