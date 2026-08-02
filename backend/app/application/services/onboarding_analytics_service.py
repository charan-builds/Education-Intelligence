from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.onboarding_event import OnboardingEvent


class OnboardingAnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def track_event(
        self,
        *,
        user_id: int,
        tenant_id: int,
        step_name: str,
        event_type: str,
        metadata: dict | None = None,
        commit: bool = True,
    ) -> None:
        event = OnboardingEvent(
            user_id=user_id,
            tenant_id=tenant_id,
            step_name=step_name,
            event_type=event_type,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=True),
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(event)
        if commit:
            await self.session.commit()
