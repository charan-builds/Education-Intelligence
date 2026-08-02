from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user_profile import UserProfile
from app.infrastructure.repositories.learning_profile_repository import LearningProfileRepository


class LearningProfileService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = LearningProfileRepository(session)

    async def build_for_user(self, *, user_id: int, tenant_id: int, user_profile: UserProfile) -> dict[str, object]:
        learning_profile = await self.repository.get_or_create_for_user(user_id=user_id, tenant_id=tenant_id)

        experience_level = str(user_profile.experience_level or "").strip().lower()
        repo_count = int(user_profile.github_repo_count or 0)
        github_activity_score = float(user_profile.github_activity_score or 0.0)
        daily_study_time = str(user_profile.daily_study_time or "")
        learning_style = str(user_profile.learning_style or "mixed")

        detected_level = self._detect_experience_level(repo_count)
        effective_level = detected_level if repo_count > 0 else (experience_level or "beginner")

        learning_speed = self._learning_speed(daily_study_time=daily_study_time, github_activity_score=github_activity_score)
        difficulty_preference = self._difficulty_preference(effective_level=effective_level, github_activity_score=github_activity_score)
        recommendation_bias = self._recommendation_bias(learning_style=learning_style, effective_level=effective_level)
        profile_type = self._profile_type(learning_style=learning_style, effective_level=effective_level)

        learning_profile.profile_type = profile_type
        learning_profile.learning_speed = learning_speed
        learning_profile.difficulty_preference = difficulty_preference
        learning_profile.recommendation_bias = recommendation_bias
        await self.session.flush()
        return {
            "profile_type": profile_type,
            "learning_speed": learning_speed,
            "difficulty_preference": difficulty_preference,
            "recommendation_bias": recommendation_bias,
            "detected_experience_level": effective_level,
        }

    async def get_for_user(self, *, user_id: int, tenant_id: int) -> dict[str, object]:
        learning_profile = await self.repository.get_for_user(user_id=user_id, tenant_id=tenant_id)
        if learning_profile is None:
            return {}
        return {
            "profile_type": learning_profile.profile_type,
            "learning_speed": float(learning_profile.learning_speed),
            "difficulty_preference": learning_profile.difficulty_preference,
            "recommendation_bias": learning_profile.recommendation_bias,
        }

    @staticmethod
    def _detect_experience_level(repo_count: int) -> str:
        if repo_count > 20:
            return "advanced"
        if 5 <= repo_count <= 20:
            return "intermediate"
        return "beginner"

    @staticmethod
    def _learning_speed(*, daily_study_time: str, github_activity_score: float) -> float:
        base = {
            "less_than_30_min": 25.0,
            "30_to_60_min": 40.0,
            "1_to_2_hours": 58.0,
            "2_to_4_hours": 75.0,
            "4_plus_hours": 88.0,
        }.get(daily_study_time, 50.0)
        return round(min(100.0, base + min(github_activity_score / 10.0, 10.0)), 2)

    @staticmethod
    def _difficulty_preference(*, effective_level: str, github_activity_score: float) -> str:
        if effective_level == "advanced" or github_activity_score >= 70:
            return "challenging"
        if effective_level == "intermediate" or github_activity_score >= 25:
            return "moderate"
        return "guided"

    @staticmethod
    def _recommendation_bias(*, learning_style: str, effective_level: str) -> str:
        if learning_style == "hands_on":
            return "project_first"
        if learning_style == "visual":
            return "concept_first"
        if effective_level == "advanced":
            return "goal_accelerated"
        return "foundations_first"

    @staticmethod
    def _profile_type(*, learning_style: str, effective_level: str) -> str:
        if learning_style == "hands_on":
            return "practice_focused"
        if learning_style in {"visual", "reading", "video"}:
            return "concept_focused"
        if effective_level == "advanced":
            return "fast_explorer"
        return "balanced"
