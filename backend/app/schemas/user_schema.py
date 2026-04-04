from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, model_validator

from app.domain.models.user import UserRole
from app.schemas.common_schema import PageMeta


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole


class UserResponse(BaseModel):
    id: int
    tenant_id: int
    email: EmailStr
    role: UserRole
    full_name: str | None = None
    display_name: str | None = None
    phone_number: str | None = None
    linkedin_url: str | None = None
    organization_name: str | None = None
    college_name: str | None = None
    avatar_url: str | None = None
    preferences: dict[str, object] = Field(default_factory=dict)
    mfa_enabled: bool = False
    is_email_verified: bool = False
    is_phone_verified: bool = False
    email_verified_at: datetime | None = None
    is_profile_completed: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    display_name: str | None = None
    phone_number: str | None = None
    linkedin_url: HttpUrl | None = None
    organization_name: str | None = None
    college_name: str | None = None
    avatar_url: str | None = None
    preferences: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_organization_alias(self) -> "UserProfileUpdateRequest":
        if self.organization_name is None and self.college_name is not None:
            self.organization_name = self.college_name
        if self.college_name is None and self.organization_name is not None:
            self.college_name = self.organization_name
        return self


class UserProfileCompletionRequest(BaseModel):
    full_name: str
    phone_number: str
    linkedin_url: HttpUrl
    organization_name: str | None = None
    college_name: str | None = None

    @model_validator(mode="after")
    def sync_organization_alias(self) -> "UserProfileCompletionRequest":
        if self.organization_name is None and self.college_name is not None:
            self.organization_name = self.college_name
        if self.college_name is None and self.organization_name is not None:
            self.college_name = self.organization_name
        return self


class UserPageResponse(BaseModel):
    items: list[UserResponse]
    meta: PageMeta
