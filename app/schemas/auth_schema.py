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
    tenant_id: int | None = None
    tenant_subdomain: str | None = None
    mfa_code: str | None = None


class TokenResponse(BaseModel):
    authenticated: bool = True
    token_type: str = "bearer"
    access_token: str
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


class EmailVerificationRequest(BaseModel):
    tenant_id: int
    email: EmailStr


class EmailVerificationConfirmRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    tenant_id: int
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    password: str


class AuthActionResponse(BaseModel):
    success: bool = True
    detail: str
    token: str | None = None


class MFASetupResponse(BaseModel):
    secret: str
    otp_auth_url: str
    manual_entry_code: str


class MFAVerifyRequest(BaseModel):
    code: str


class ActiveSessionResponse(BaseModel):
    id: str
    device: str | None = None
    created_at: str
    expires_at: str
