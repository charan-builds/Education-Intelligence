from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.analytics_service import AnalyticsService
from app.core.dependencies import require_roles
from app.infrastructure.database import get_db_session
from app.schemas.analytics_schema import (
    AnalyticsOverviewResponse,
    PlatformAnalyticsOverviewResponse,
    RetentionAnalyticsResponse,
    RoadmapProgressSummaryResponse,
    TopicMasteryAnalyticsResponse,
)
from app.application.services.retention_service import RetentionService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    return await AnalyticsService(db).aggregated_metrics(current_user.tenant_id)


@router.get("/roadmap-progress", response_model=RoadmapProgressSummaryResponse)
async def get_roadmap_progress_analytics(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    return await AnalyticsService(db).roadmap_progress_summary(current_user.tenant_id)


@router.get("/topic-mastery", response_model=TopicMasteryAnalyticsResponse)
async def get_topic_mastery_analytics(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    return await AnalyticsService(db).topic_mastery_summary(current_user.tenant_id)


@router.get("/platform-overview", response_model=PlatformAnalyticsOverviewResponse)
async def get_platform_analytics_overview(
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin")),
):
    return await AnalyticsService(db).platform_overview()


@router.get("/retention", response_model=RetentionAnalyticsResponse)
async def get_retention_analytics(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    return await RetentionService(db).tenant_retention_summary(tenant_id=current_user.tenant_id)
