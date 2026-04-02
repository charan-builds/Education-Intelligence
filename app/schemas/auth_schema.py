from pydantic import BaseModel, EmailStr

from app.domain.models.user import UserRole
from app.schemas.user_schema import UserResponse


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: int | None = None
    role: UserRole = UserRole.independent_learner
    full_name: str | None = None
    invite_token: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: int | None = None
    tenant_subdomain: str | None = None
    mfa_code: str | None = None


class TokenResponse(BaseModel):
    authenticated: bool = True
    requires_profile_completion: bool = False
    token_type: str = "bearer"
    scope: str = "full_access"
    access_token: str | None = None
    access_token_expires_in: int | None = None
    refresh_token_expires_in: int | None = None
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


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
    tenant_id: int | None = None
    email: EmailStr


class EmailVerificationConfirmRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    tenant_id: int | None = None
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


class OTPRequest(BaseModel):
    phone_number: str | None = None


class OTPVerifyRequest(BaseModel):
    code: str


class ActiveSessionResponse(BaseModel):
    id: str
    device: str | None = None
    created_at: str
    expires_at: str
