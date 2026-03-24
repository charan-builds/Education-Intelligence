from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.career_service import CareerService
from app.core.dependencies import get_current_user, require_roles
from app.domain.models.job_role import JobRole
from app.domain.models.job_role_skill import JobRoleSkill
from app.infrastructure.database import get_db_session
from app.schemas.career_schema import (
    CareerOverviewResponse,
    InterviewPrepRequest,
    InterviewPrepResponse,
    JobReadinessResponse,
    ResumePreviewResponse,
)

router = APIRouter(prefix="/career", tags=["career"])


@router.get("/overview", response_model=CareerOverviewResponse)
async def career_overview(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return CareerOverviewResponse(**(await CareerService(db).get_overview(user_id=current_user.id, tenant_id=current_user.tenant_id)))


@router.get("/readiness", response_model=JobReadinessResponse)
async def career_readiness(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return JobReadinessResponse(**(await CareerService(db).get_job_readiness(user_id=current_user.id, tenant_id=current_user.tenant_id)))


@router.get("/resume", response_model=ResumePreviewResponse)
async def career_resume(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return ResumePreviewResponse(**(await CareerService(db).get_resume_preview(user_id=current_user.id, tenant_id=current_user.tenant_id)))


@router.post("/interview-prep", response_model=InterviewPrepResponse)
async def interview_prep(
    payload: InterviewPrepRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return InterviewPrepResponse(**(
        await CareerService(db).get_interview_prep(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            role_name=payload.role_name,
            difficulty=payload.difficulty,
            count=payload.count,
        )
    ))


@router.post("/roles/bootstrap")
async def bootstrap_career_roles(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    roles = [
        ("Data Analyst", "analytics"),
        ("ML Engineer", "ai"),
        ("Frontend Engineer", "software"),
        ("Backend Engineer", "software"),
    ]
    created = 0
    for name, category in roles:
        row = JobRole(
            tenant_id=current_user.tenant_id,
            name=name,
            category=category,
            description=f"{name} career track generated from platform learning data.",
            created_at=datetime.now(timezone.utc),
        )
        db.add(row)
        created += 1
    await db.commit()
    return {"created": created}
