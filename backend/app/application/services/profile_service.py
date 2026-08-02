from __future__ import annotations

import base64

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import ValidationError
from app.application.services.github_profile_service import GitHubProfileService
from app.application.services.learning_profile_service import LearningProfileService
from app.application.services.onboarding_analytics_service import OnboardingAnalyticsService
from app.domain.models.user_profile import UserProfile
from app.infrastructure.repositories.user_profile_repository import UserProfileRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.schemas.profile_schema import UserProfileUpsertRequest


class ProfileService:
    REQUIRED_FIELDS = (
        "full_name",
        "college_name",
        "degree",
        "year_of_study",
        "experience_level",
        "daily_study_time",
        "learning_style",
        "learning_goal_note",
        "target_timeline",
    )
    ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
    MAX_PHOTO_BYTES = 2 * 1024 * 1024

    def __init__(self, session: AsyncSession):
        self.session = session
        self.profile_repository = UserProfileRepository(session)
        self.user_repository = UserRepository(session)
        self.github_profile_service = GitHubProfileService()
        self.learning_profile_service = LearningProfileService(session)
        self.onboarding_analytics_service = OnboardingAnalyticsService(session)

    async def get_profile(self, *, user_id: int, tenant_id: int) -> UserProfile:
        profile = await self.profile_repository.get_for_user(user_id=user_id, tenant_id=tenant_id)
        if profile is not None:
            return profile
        return await self.profile_repository.get_or_create_for_user(user_id=user_id, tenant_id=tenant_id)

    async def get_status(self, *, user_id: int, tenant_id: int) -> dict:
        profile = await self.get_profile(user_id=user_id, tenant_id=tenant_id)
        missing = self._missing_required_fields(profile)
        return {
            "user_id": user_id,
            "profile_completed": bool(profile.profile_completed),
            "required_fields_completed": len(missing) == 0,
            "missing_required_fields": missing,
        }

    async def get_progress(self, *, user_id: int, tenant_id: int) -> dict:
        profile = await self.get_profile(user_id=user_id, tenant_id=tenant_id)
        missing = self._missing_required_fields(profile)
        completion_percent = round(((len(self.REQUIRED_FIELDS) - len(missing)) / max(len(self.REQUIRED_FIELDS), 1)) * 100)
        return {
            "completion_percent": int(max(0, min(100, completion_percent))),
            "missing_fields": missing,
        }

    async def upsert_profile(
        self,
        *,
        user_id: int,
        tenant_id: int,
        payload: UserProfileUpsertRequest,
    ) -> UserProfile:
        try:
            user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
            if user is None:
                raise ValidationError("User not found")
            profile = await self.profile_repository.get_or_create_for_user(user_id=user_id, tenant_id=tenant_id)
            updates = payload.model_dump(exclude_unset=True)
            requested_completion = updates.pop("profile_completed", None)
            for field_name, value in updates.items():
                setattr(profile, field_name, self._normalize_string(value))

            if profile.github_url:
                try:
                    github_summary = await self.github_profile_service.fetch_summary(profile.github_url)
                except Exception:
                    github_summary = {}
                for field_name, value in github_summary.items():
                    setattr(profile, field_name, value)
                detected_level = self.learning_profile_service._detect_experience_level(int(profile.github_repo_count or 0))
                if detected_level:
                    profile.experience_level = detected_level

            missing_required_fields = self._missing_required_fields(profile)
            if requested_completion is True and missing_required_fields:
                raise ValidationError(
                    "Profile is missing required fields: " + ", ".join(missing_required_fields)
                )
            profile.profile_completed = bool(requested_completion) if requested_completion is not None else bool(profile.profile_completed and not missing_required_fields)
            self._sync_user_shadow_fields(user=user, profile=profile)
            if profile.profile_completed:
                await self.learning_profile_service.build_for_user(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    user_profile=profile,
                )
            await self.session.commit()
            await self.session.refresh(profile)
            return profile
        except Exception:
            await self.session.rollback()
            raise

    async def upload_photo(
        self,
        *,
        user_id: int,
        tenant_id: int,
        photo: UploadFile,
    ) -> str:
        try:
            if photo.content_type not in self.ALLOWED_PHOTO_TYPES:
                raise ValidationError("Profile photo must be JPEG, PNG, or WebP")
            raw = await photo.read()
            if not raw:
                raise ValidationError("Uploaded profile photo is empty")
            if len(raw) > self.MAX_PHOTO_BYTES:
                raise ValidationError("Profile photo exceeds the 2MB limit")

            encoded = base64.b64encode(raw).decode("ascii")
            data_url = f"data:{photo.content_type};base64,{encoded}"
            profile = await self.profile_repository.get_or_create_for_user(user_id=user_id, tenant_id=tenant_id)
            user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
            if user is None:
                raise ValidationError("User not found")
            profile.profile_photo_url = data_url
            self._sync_user_shadow_fields(user=user, profile=profile)
            await self.session.commit()
            return data_url
        except Exception:
            await self.session.rollback()
            raise

    def _missing_required_fields(self, profile: UserProfile) -> list[str]:
        missing: list[str] = []
        for field_name in self.REQUIRED_FIELDS:
            value = getattr(profile, field_name, None)
            if value is None:
                missing.append(field_name)
                continue
            if isinstance(value, str) and not value.strip():
                missing.append(field_name)
        return missing

    @staticmethod
    def _normalize_string(value):
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value

    @staticmethod
    def _sync_user_shadow_fields(*, user, profile: UserProfile) -> None:
        if profile.full_name:
            user.full_name = profile.full_name
            user.display_name = profile.full_name
        if profile.linkedin_url is not None:
            user.linkedin_url = profile.linkedin_url
        if profile.college_name is not None:
            user.college_name = profile.college_name
        if profile.profile_photo_url is not None:
            user.avatar_url = profile.profile_photo_url
        user.is_profile_completed = bool(profile.profile_completed)
