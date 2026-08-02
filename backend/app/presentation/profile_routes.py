from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.onboarding_analytics_service import OnboardingAnalyticsService
from app.application.services.profile_service import ProfileService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.schemas.profile_schema import (
    OnboardingEventRequest,
    UserProfilePhotoUploadResponse,
    UserProfileProgressResponse,
    UserProfileResponse,
    UserProfileStatusResponse,
    UserProfileUpsertRequest,
)

router = APIRouter(prefix="/profile", tags=["profile"])


def _serialize_profile(profile) -> UserProfileResponse:
    return UserProfileResponse.model_validate(profile)


@router.get("", response_model=UserProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    profile = await ProfileService(db).get_profile(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    return _serialize_profile(profile)


@router.post("", response_model=UserProfileResponse)
async def create_or_update_profile(
    payload: UserProfileUpsertRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    profile = await ProfileService(db).upsert_profile(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        payload=payload,
    )
    return _serialize_profile(profile)


@router.get("/status", response_model=UserProfileStatusResponse)
async def profile_status(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await ProfileService(db).get_status(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )


@router.get("/progress", response_model=UserProfileProgressResponse)
async def profile_progress(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await ProfileService(db).get_progress(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )


@router.post("/upload-photo", response_model=UserProfilePhotoUploadResponse)
async def upload_profile_photo(
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    profile_photo_url = await ProfileService(db).upload_photo(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        photo=photo,
    )
    return UserProfilePhotoUploadResponse(profile_photo_url=profile_photo_url)


@router.post("/onboarding-events", status_code=204)
async def track_onboarding_event(
    payload: OnboardingEventRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    await OnboardingAnalyticsService(db).track_event(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        step_name=payload.step_name,
        event_type=payload.event_type,
        metadata=payload.metadata,
        commit=True,
    )
