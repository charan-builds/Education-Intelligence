from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.ai_request import AIRequest


class AIRequestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        tenant_id: int,
        user_id: int,
        request_id: str,
        request_type: str,
        payload: dict,
        max_attempts: int = 3,
    ) -> AIRequest:
        row = AIRequest(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            request_type=request_type,
            status="queued",
            payload_json=json.dumps(payload, ensure_ascii=True, default=str),
            result_json=None,
            error_message=None,
            provider=None,
            attempt_count=0,
            max_attempts=max_attempts,
            created_at=datetime.now(timezone.utc),
            started_at=None,
            completed_at=None,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_by_request_id(self, *, tenant_id: int, user_id: int, request_id: str) -> AIRequest | None:
        result = await self.session.execute(
            select(AIRequest).where(
                AIRequest.tenant_id == tenant_id,
                AIRequest.user_id == user_id,
                AIRequest.request_id == request_id,
            )
        )
        return result.scalar_one_or_none()

    async def mark_processing(self, row: AIRequest) -> AIRequest:
        row.status = "processing"
        row.attempt_count = int(row.attempt_count) + 1
        row.started_at = datetime.now(timezone.utc)
        row.error_message = None
        await self.session.flush()
        return row

    async def mark_completed(self, row: AIRequest, *, result: dict, provider: str | None = None) -> AIRequest:
        row.status = "completed"
        row.result_json = json.dumps(result, ensure_ascii=True, default=str)
        row.provider = provider
        row.error_message = None
        row.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return row

    async def mark_fallback(self, row: AIRequest, *, result: dict, error_message: str | None = None) -> AIRequest:
        row.status = "fallback"
        row.result_json = json.dumps(result, ensure_ascii=True, default=str)
        row.error_message = error_message[:512] if error_message else None
        row.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return row

    async def mark_failed(self, row: AIRequest, *, error_message: str, timed_out: bool = False) -> AIRequest:
        row.status = "timed_out" if timed_out else "failed"
        row.error_message = error_message[:512]
        row.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return row
