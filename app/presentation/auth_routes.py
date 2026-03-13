from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.auth_service import AuthService
from app.infrastructure.database import get_db_session
from app.presentation.middleware.rate_limiter import limiter, rate_limit_key_by_ip, rate_limit_key_by_user
from app.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user_schema import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db_session)):
    service = AuthService(db)
    return await service.register(
        tenant_id=payload.tenant_id,
        email=payload.email,
        password=payload.password,
        role=payload.role,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("50/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("100/minute", key_func=rate_limit_key_by_user)
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    service = AuthService(db)
    token, _ = await service.login(payload.email, payload.password)
    return TokenResponse(access_token=token)
