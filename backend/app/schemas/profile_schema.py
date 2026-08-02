from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


EXPERIENCE_LEVELS = {
    "beginner",
    "intermediate",
    "advanced",
}

DAILY_STUDY_TIME_OPTIONS = {
    "less_than_30_min",
    "30_to_60_min",
    "1_to_2_hours",
    "2_to_4_hours",
    "4_plus_hours",
}

LEARNING_STYLE_OPTIONS = {
    "visual",
    "reading",
    "hands_on",
    "video",
    "mixed",
}

TARGET_TIMELINE_OPTIONS = {
    "1_month",
    "3_months",
    "6_months",
    "12_months",
    "flexible",
}


class UserProfileResponse(BaseModel):
    user_id: int
    full_name: str | None = None
    profile_photo_url: str | None = None
    bio: str | None = None
    college_name: str | None = None
    degree: str | None = None
    year_of_study: int | None = None
    github_url: str | None = None
    github_repo_count: int | None = None
    github_languages: list[str] | None = None
    github_activity_score: float | None = None
    leetcode_url: str | None = None
    hackerrank_url: str | None = None
    linkedin_url: str | None = None
    experience_level: str | None = None
    daily_study_time: str | None = None
    learning_style: str | None = None
    learning_goal_note: str | None = None
    target_timeline: str | None = None
    profile_completed: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpsertRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    profile_photo_url: str | None = Field(default=None, max_length=4096)
    bio: str | None = Field(default=None, max_length=2000)
    college_name: str | None = Field(default=None, max_length=255)
    degree: str | None = Field(default=None, max_length=255)
    year_of_study: int | None = Field(default=None, ge=1, le=12)
    github_url: HttpUrl | None = None
    leetcode_url: HttpUrl | None = None
    hackerrank_url: HttpUrl | None = None
    linkedin_url: HttpUrl | None = None
    experience_level: str | None = Field(default=None, max_length=64)
    daily_study_time: str | None = Field(default=None, max_length=64)
    learning_style: str | None = Field(default=None, max_length=64)
    learning_goal_note: str | None = Field(default=None, max_length=2000)
    target_timeline: str | None = Field(default=None, max_length=128)
    profile_completed: bool | None = None

    @model_validator(mode="after")
    def validate_domains(self) -> "UserProfileUpsertRequest":
        self._validate_allowed_domain("github_url", "github.com")
        self._validate_allowed_domain("linkedin_url", "linkedin.com")
        self._validate_allowed_domain("leetcode_url", "leetcode.com")
        self._validate_allowed_domain("hackerrank_url", "hackerrank.com")
        self._validate_enum("experience_level", EXPERIENCE_LEVELS)
        self._validate_enum("daily_study_time", DAILY_STUDY_TIME_OPTIONS)
        self._validate_enum("learning_style", LEARNING_STYLE_OPTIONS)
        self._validate_enum("target_timeline", TARGET_TIMELINE_OPTIONS)
        return self

    def _validate_allowed_domain(self, field_name: str, expected_domain: str) -> None:
        value = getattr(self, field_name)
        if value is None:
            return
        host = value.host.lower() if value.host else ""
        if expected_domain not in host:
            raise ValueError(f"{field_name} must point to {expected_domain}")

    def _validate_enum(self, field_name: str, allowed_values: set[str]) -> None:
        value = getattr(self, field_name)
        if value is None:
            return
        if value not in allowed_values:
            raise ValueError(f"{field_name} must be one of: {', '.join(sorted(allowed_values))}")


class UserProfileStatusResponse(BaseModel):
    user_id: int
    profile_completed: bool
    required_fields_completed: bool
    missing_required_fields: list[str]


class UserProfileProgressResponse(BaseModel):
    completion_percent: int
    missing_fields: list[str]


class UserProfilePhotoUploadResponse(BaseModel):
    profile_photo_url: str


class OnboardingEventRequest(BaseModel):
    step_name: str = Field(min_length=1, max_length=64)
    event_type: str = Field(min_length=1, max_length=32)
    metadata: dict[str, object] = Field(default_factory=dict)
