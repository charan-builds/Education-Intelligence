from pydantic import BaseModel, EmailStr

from app.domain.models.user import UserRole


class RegisterRequest(BaseModel):
    tenant_id: int = 1
    email: EmailStr
    password: str
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
