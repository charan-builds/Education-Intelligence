from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.mentor_message import MentorMessage


class MentorMessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_message(
        self,
        *,
        tenant_id: int,
        user_id: int,
        request_id: str,
        role: str,
        message: str,
    ) -> MentorMessage:
        existing = await self.get_by_request(request_id=request_id, tenant_id=tenant_id, user_id=user_id)
        if existing is not None:
            return existing

        now = datetime.now(timezone.utc)
        msg = MentorMessage(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            role=role,
            message=message,
            status="pending",
            created_at=now,
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def set_response(self, *, request_id: str, response: str, status: str) -> MentorMessage | None:
        stmt = select(MentorMessage).where(MentorMessage.request_id == request_id)
        result = await self.session.execute(stmt)
        msg = result.scalar_one_or_none()
        if msg is None:
            return None
        msg.response = response
        msg.status = status
        await self.session.flush()
        return msg

    async def mark_acked(self, *, request_id: str) -> MentorMessage | None:
        return await self.set_response(request_id=request_id, response=None, status="delivered")

    async def get_by_request(self, *, request_id: str, tenant_id: int, user_id: int) -> MentorMessage | None:
        stmt = select(MentorMessage).where(
            MentorMessage.request_id == request_id,
            MentorMessage.tenant_id == tenant_id,
            MentorMessage.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent_messages(self, *, tenant_id: int, user_id: int, limit: int = 20) -> list[MentorMessage]:
        stmt = (
            select(MentorMessage)
            .where(MentorMessage.tenant_id == tenant_id, MentorMessage.user_id == user_id)
            .order_by(MentorMessage.created_at.desc(), MentorMessage.id.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(reversed(list(result.scalars().all())))
