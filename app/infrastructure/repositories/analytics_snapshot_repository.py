from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.analytics_snapshot import AnalyticsSnapshot


class AnalyticsSnapshotRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_snapshot(
        self,
        *,
        tenant_id: int | None,
        snapshot_type: str,
        subject_id: int | None,
        payload_json: str,
        window_start: datetime,
        window_end: datetime,
        updated_at: datetime,
    ) -> AnalyticsSnapshot:
        row = await self.session.scalar(
            select(AnalyticsSnapshot).where(
                AnalyticsSnapshot.tenant_id == tenant_id,
                AnalyticsSnapshot.snapshot_type == snapshot_type,
                AnalyticsSnapshot.subject_id == subject_id,
                AnalyticsSnapshot.window_start == window_start,
                AnalyticsSnapshot.window_end == window_end,
            )
        )
        if row is None:
            row = AnalyticsSnapshot(
                tenant_id=tenant_id,
                snapshot_type=snapshot_type,
                subject_id=subject_id,
                payload_json=payload_json,
                window_start=window_start,
                window_end=window_end,
                updated_at=updated_at,
            )
            self.session.add(row)
        else:
            row.payload_json = payload_json
            row.updated_at = updated_at
        await self.session.flush()
        return row

    async def latest_snapshot(
        self,
        *,
        tenant_id: int | None,
        snapshot_type: str,
        subject_id: int | None,
    ) -> AnalyticsSnapshot | None:
        result = await self.session.execute(
            select(AnalyticsSnapshot)
            .where(
                AnalyticsSnapshot.tenant_id == tenant_id,
                AnalyticsSnapshot.snapshot_type == snapshot_type,
                AnalyticsSnapshot.subject_id == subject_id,
            )
            .order_by(AnalyticsSnapshot.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
