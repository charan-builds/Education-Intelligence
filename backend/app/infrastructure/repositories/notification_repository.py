from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        tenant_id: int,
        user_id: int,
        notification_type: str,
        severity: str,
        priority: str,
        title: str,
        message: str,
        metadata_json: str,
        dedupe_key: str | None,
        action_url: str | None,
        scheduled_for: datetime | None,
        created_at: datetime,
    ) -> Notification:
        row = Notification(
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type=notification_type,
            severity=severity,
            priority=priority,
            title=title,
            message=message,
            metadata_json=metadata_json,
            dedupe_key=dedupe_key,
            action_url=action_url,
            scheduled_for=scheduled_for,
            created_at=created_at,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_for_user(self, *, tenant_id: int, user_id: int, unread_only: bool, limit: int) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.tenant_id == tenant_id, Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            stmt = stmt.where(Notification.read_at.is_(None))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(self, *, tenant_id: int, user_id: int, notification_id: int) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.tenant_id == tenant_id,
                Notification.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def mark_read(self, notification: Notification, *, read_at: datetime) -> Notification:
        notification.read_at = read_at
        await self.session.flush()
        return notification

    async def find_recent_duplicate(
        self,
        *,
        tenant_id: int,
        user_id: int,
        notification_type: str,
        title: str,
        window_hours: int = 24,
    ) -> Notification | None:
        threshold = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        result = await self.session.execute(
            select(Notification)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.user_id == user_id,
                Notification.notification_type == notification_type,
                Notification.title == title,
                Notification.created_at >= threshold,
            )
            .order_by(Notification.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def find_by_dedupe_key(self, *, tenant_id: int, user_id: int, dedupe_key: str) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.tenant_id == tenant_id,
                Notification.user_id == user_id,
                Notification.dedupe_key == dedupe_key,
            )
        )
        return result.scalar_one_or_none()
