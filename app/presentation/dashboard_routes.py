from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.dashboard_service import DashboardService
from app.core.dependencies import get_current_user, require_roles
from app.infrastructure.database import get_db_session
from app.schemas.dashboard_schema import (
    AdminDashboardResponse,
    CommunityIntelligenceResponse,
    ExperimentSummaryResponse,
    StudentDashboardResponse,
    TeacherAnalyticsResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/student", response_model=StudentDashboardResponse)
async def get_student_dashboard(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("student")),
):
    return await DashboardService(db).student_dashboard(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )


@router.get("/admin", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    return await DashboardService(db).admin_dashboard(tenant_id=current_user.tenant_id)


@router.get("/teacher", response_model=TeacherAnalyticsResponse)
async def get_teacher_dashboard(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "admin", "super_admin")),
):
    return await DashboardService(db).teacher_dashboard(tenant_id=current_user.tenant_id)


@router.get("/experiments", response_model=ExperimentSummaryResponse)
async def get_experiment_dashboard(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    return await DashboardService(db).experiment_dashboard(tenant_id=current_user.tenant_id)


@router.get("/community", response_model=CommunityIntelligenceResponse)
async def get_community_dashboard(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    return await DashboardService(db).community_dashboard(tenant_id=current_user.tenant_id)
