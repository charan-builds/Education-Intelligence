from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.auth_service import AuthService
from app.core.config import get_settings
from app.core.dependencies import require_roles
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME
from app.domain.models.user import UserRole
from app.infrastructure.database import get_db_session
from app.presentation.middleware.rate_limiter import limiter, rate_limit_key_by_ip, rate_limit_key_by_user
from app.schemas.auth_schema import InviteCreateRequest, InviteResponse, LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user_schema import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookie(response: Response, *, key: str, value: str, max_age: int) -> None:
    settings = get_settings()
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        max_age=max_age,
        expires=max_age,
        path="/",
        domain=settings.auth_cookie_domain,
    )


def _set_auth_cookies(response: Response, *, access_token: str, refresh_token: str) -> None:
    settings = get_settings()
    _set_cookie(
        response,
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
    )
    _set_cookie(
        response,
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.refresh_token_expire_minutes * 60,
    )


def _clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME, path="/", domain=settings.auth_cookie_domain)
    response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME, path="/", domain=settings.auth_cookie_domain)


@router.post("/register", response_model=UserResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db_session)):
    return await AuthService(db).register(
        email=payload.email,
        password=payload.password,
        invite_token=payload.invite_token,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("50/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("100/minute", key_func=rate_limit_key_by_user)
async def login(request: Request, response: Response, payload: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    access_token, refresh_token, user = await AuthService(db).login(
        payload.email,
        payload.password,
        device=request.headers.get("user-agent"),
    )
    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    settings = get_settings()
    return TokenResponse(
        access_token_expires_in=settings.access_token_expire_minutes * 60,
        refresh_token_expires_in=settings.refresh_token_expire_minutes * 60,
        user=user,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("120/minute", key_func=rate_limit_key_by_ip)
async def refresh_session(request: Request, response: Response, db: AsyncSession = Depends(get_db_session)):
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
    access_token, next_refresh_token, user = await AuthService(db).refresh_session(
        refresh_token,
        device=request.headers.get("user-agent"),
    )
    _set_auth_cookies(response, access_token=access_token, refresh_token=next_refresh_token)
    settings = get_settings()
    return TokenResponse(
        access_token_expires_in=settings.access_token_expire_minutes * 60,
        refresh_token_expires_in=settings.refresh_token_expire_minutes * 60,
        user=user,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db_session)):
    await AuthService(db).logout(request.cookies.get(REFRESH_TOKEN_COOKIE_NAME))
    _clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/invites", response_model=InviteResponse)
async def create_invite(
    payload: InviteCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("super_admin", "admin")),
):
    invite_token = await AuthService(db).create_invite(
        actor_role=current_user.role if isinstance(current_user.role, UserRole) else UserRole(str(current_user.role)),
        tenant_id=current_user.tenant_id,
        role=payload.role,
        email=payload.email,
    )
    settings = get_settings()
    frontend_origin = next(
        (origin.strip().rstrip("/") for origin in settings.cors_origins.split(",") if origin.strip()),
        str(request.base_url).rstrip("/"),
    )
    return InviteResponse(
        invite_token=invite_token,
        invite_url=f"{frontend_origin}/auth?invite={invite_token}",
        email=payload.email,
        role=payload.role,
        expires_in_hours=settings.invite_token_expire_hours,
    )
