from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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
    display_name: str | None = None
    avatar_url: str | None = None
    preferences: dict[str, object] = Field(default_factory=dict)
    mfa_enabled: bool = False
    email_verified_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    preferences: dict[str, object] = Field(default_factory=dict)


class UserPageResponse(BaseModel):
    items: list[UserResponse]
    meta: PageMeta
