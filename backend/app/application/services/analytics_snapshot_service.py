from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.analytics_snapshot_repository import AnalyticsSnapshotRepository


class AnalyticsSnapshotService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = AnalyticsSnapshotRepository(session)

    async def write_snapshot(self, tenant_id, snapshot_type, data, *, subject_id: int | None = None):
        """
        Insert new snapshot.
        Mark previous snapshot as is_latest = False.
        Maintain version increment.
        """
        now = datetime.now(timezone.utc)
        resolved_subject_id = subject_id
        if resolved_subject_id is None and isinstance(data, dict):
            raw_subject_id = data.get("subject_id")
            if isinstance(raw_subject_id, int):
                resolved_subject_id = raw_subject_id

        snapshot = await self.repository.create_snapshot_version(
            tenant_id=tenant_id,
            snapshot_type=snapshot_type,
            subject_id=resolved_subject_id,
            payload_json=json.dumps(data, ensure_ascii=True, default=str),
            window_start=now,
            window_end=now,
            updated_at=now,
        )
        await self.session.commit()
        return snapshot

    async def get_latest_snapshot(self, tenant_id, snapshot_type, *, subject_id: int | None = None):
        """
        Always return latest snapshot where is_latest = True.
        Never compute live.
        """
        snapshot = await self.repository.latest_snapshot(
            tenant_id=tenant_id,
            snapshot_type=snapshot_type,
            subject_id=subject_id,
        )
        if snapshot is None:
            return None

        if getattr(snapshot, "data", None) is not None:
            payload: Any = snapshot.data
        else:
            payload = json.loads(snapshot.payload_json)

        return {
            "id": snapshot.id,
            "tenant_id": snapshot.tenant_id,
            "snapshot_type": snapshot.snapshot_type,
            "data": payload,
            "version": getattr(snapshot, "version", snapshot.snapshot_version),
            "created_at": snapshot.created_at,
            "is_latest": snapshot.is_latest,
        }

    async def get_snapshot_age(self, tenant_id, snapshot_type, *, subject_id: int | None = None):
        latest = await self.get_latest_snapshot(
            tenant_id,
            snapshot_type,
            subject_id=subject_id,
        )
        if latest is None or latest.get("created_at") is None:
            return None

        created_at = latest["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - created_at.astimezone(timezone.utc)
