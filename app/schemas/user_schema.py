from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPageResponse(BaseModel):
    items: list[UserResponse]
    meta: PageMeta
