from pydantic import BaseModel, EmailStr

from app.domain.models.user import UserRole
from app.schemas.user_schema import UserResponse


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    invite_token: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    authenticated: bool = True
    token_type: str = "cookie"
    access_token_expires_in: int
    refresh_token_expires_in: int | None = None
    user: UserResponse


class InviteCreateRequest(BaseModel):
    email: EmailStr | None = None
    role: UserRole


class InviteResponse(BaseModel):
    invite_token: str
    invite_url: str
    email: EmailStr | None = None
    role: UserRole
    expires_in_hours: int
