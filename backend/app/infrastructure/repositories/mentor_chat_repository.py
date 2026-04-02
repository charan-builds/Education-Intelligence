from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.mentor_chat_message import MentorChatMessage


class MentorChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_message(
        self,
        *,
        tenant_id: int,
        user_id: int,
        request_id: str,
        direction: str,
        channel: str,
        status: str,
        content: str,
        response_json: dict | None = None,
    ) -> MentorChatMessage:
        row = MentorChatMessage(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            direction=direction,
            channel=channel,
            status=status,
            content=content,
            response_json=json.dumps(response_json, ensure_ascii=True, default=str) if response_json is not None else None,
            retry_count=0,
            created_at=datetime.now(timezone.utc),
            delivered_at=None,
            acked_at=None,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_by_request(
        self,
        *,
        tenant_id: int,
        user_id: int,
        request_id: str,
        direction: str,
    ) -> MentorChatMessage | None:
        result = await self.session.execute(
            select(MentorChatMessage).where(
                MentorChatMessage.tenant_id == tenant_id,
                MentorChatMessage.user_id == user_id,
                MentorChatMessage.request_id == request_id,
                MentorChatMessage.direction == direction,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_message(
        self,
        *,
        tenant_id: int,
        user_id: int,
        request_id: str,
        direction: str,
        channel: str,
        status: str,
        content: str,
        response_json: dict | None = None,
    ) -> MentorChatMessage:
        existing = await self.get_by_request(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            direction=direction,
        )
        if existing is not None:
            existing.channel = channel
            existing.status = status
            existing.content = content
            existing.response_json = json.dumps(response_json, ensure_ascii=True, default=str) if response_json is not None else None
            existing.retry_count = int(existing.retry_count) + 1
            await self.session.flush()
            return existing
        return await self.create_message(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            direction=direction,
            channel=channel,
            status=status,
            content=content,
            response_json=response_json,
        )

    async def mark_delivered(self, row: MentorChatMessage) -> MentorChatMessage:
        row.status = "delivered"
        row.delivered_at = datetime.now(timezone.utc)
        await self.session.flush()
        return row

    async def mark_acked(self, row: MentorChatMessage) -> MentorChatMessage:
        row.status = "acked"
        row.acked_at = datetime.now(timezone.utc)
        await self.session.flush()
        return row
