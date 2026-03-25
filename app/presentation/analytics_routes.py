from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.analytics_service import AnalyticsService
from app.application.services.skill_vector_service import SkillVectorService
from app.core.dependencies import get_current_user
from app.core.dependencies import get_pagination_params, require_roles
from app.infrastructure.database import get_db_session
from app.schemas.common_schema import PaginationParams
from app.schemas.analytics_schema import (
    AnalyticsOverviewResponse,
    LearnerIntelligenceOverviewResponse,
    LearnerSkillVectorResponse,
    LearningTrendPointResponse,
    PlatformAnalyticsOverviewResponse,
    RetentionAnalyticsResponse,
    RoadmapProgressSummaryResponse,
    WeakTopicInsightResponse,
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
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await AnalyticsService(db).roadmap_progress_summary(
        current_user.tenant_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )


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


@router.get("/student-insights", response_model=LearnerIntelligenceOverviewResponse)
async def get_student_insights(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    payload = await SkillVectorService(db).aggregated_feature_payload(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    return {
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id,
        **payload,
    }


@router.get("/skill-vectors", response_model=LearnerSkillVectorResponse)
async def get_skill_vectors(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    vectors = await SkillVectorService(db).learner_vectors(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    return {
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id,
        "vectors": vectors,
    }


@router.get("/weak-topics", response_model=list[WeakTopicInsightResponse])
async def get_weak_topics(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    return await SkillVectorService(db).weak_topics(tenant_id=current_user.tenant_id)


@router.get("/learning-trends", response_model=list[LearningTrendPointResponse])
async def get_learning_trends(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    return await SkillVectorService(db).learning_trends(tenant_id=current_user.tenant_id)
