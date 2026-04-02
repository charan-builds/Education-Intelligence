from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.application.services.analytics_service import AnalyticsService
from app.application.services.community_service import CommunityService
from app.application.services.dashboard_service import DashboardService
from app.domain.models.user import User, UserRole
from app.infrastructure.database import AsyncSessionLocal


OUTPUT_DIR = Path("docs/demo_api_samples")


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    async with AsyncSessionLocal() as session:
        student = (
            await session.execute(select(User).where(User.role == UserRole.student).order_by(User.id.asc()))
        ).scalars().first()
        teacher = (
            await session.execute(select(User).where(User.role == UserRole.teacher).order_by(User.id.asc()))
        ).scalars().first()

        if student is None or teacher is None:
            raise RuntimeError("Seed data is missing. Run python seed.py first.")

        dashboard_service = DashboardService(session)
        analytics_service = AnalyticsService(session)
        community_service = CommunityService(session)

        student_dashboard = await dashboard_service.student_dashboard(user_id=student.id, tenant_id=student.tenant_id)
        teacher_dashboard = await dashboard_service.teacher_dashboard(tenant_id=teacher.tenant_id)
        overview = await analytics_service.aggregated_metrics(teacher.tenant_id)
        roadmap_progress = await analytics_service.roadmap_progress_summary(teacher.tenant_id)
        communities = await community_service.list_communities_page(
            tenant_id=teacher.tenant_id,
            user_id=teacher.id,
            limit=5,
            offset=0,
            topic_id=None,
        )
        threads = await community_service.list_threads_page(
            tenant_id=teacher.tenant_id,
            limit=5,
            offset=0,
            community_id=None,
        )

        payloads = {
            "student_dashboard.json": student_dashboard,
            "teacher_dashboard.json": teacher_dashboard,
            "analytics_overview.json": overview,
            "roadmap_progress.json": roadmap_progress,
            "communities.json": communities,
            "threads.json": threads,
        }

        for filename, payload in payloads.items():
            (OUTPUT_DIR / filename).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print(f"Wrote demo API samples to {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
