from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.auth_service import AuthService
from app.core.config import get_settings
from app.core.dependencies import get_current_user, require_roles
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME, decode_access_token
from app.domain.models.user import UserRole
from app.infrastructure.database import get_db_session
from app.presentation.middleware.rate_limiter import limiter, rate_limit_key_by_ip, rate_limit_key_by_user
from app.schemas.auth_schema import (
    ActiveSessionResponse,
    AuthActionResponse,
    EmailVerificationConfirmRequest,
    EmailVerificationRequest,
    InviteCreateRequest,
    InviteResponse,
    LoginRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user_schema import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _serialize_user(user, *, tenant_id: int, role) -> UserResponse:
    return UserResponse.model_validate(
        {
            "id": int(user.id),
            "tenant_id": tenant_id,
            "email": user.email,
            "role": role,
            "display_name": getattr(user, "display_name", None),
            "avatar_url": getattr(user, "avatar_url", None),
            "preferences": getattr(user, "preferences_json", None) or {},
            "mfa_enabled": bool(getattr(user, "mfa_enabled", False)),
            "email_verified_at": getattr(user, "email_verified_at", None),
            "created_at": user.created_at,
        }
    )


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
    user = await AuthService(db).register(
        email=payload.email,
        password=payload.password,
        invite_token=payload.invite_token,
    )
    tenant_id = int(payload.tenant_id) if getattr(payload, "tenant_id", None) is not None else int(user.tenant_id)
    return _serialize_user(user, tenant_id=tenant_id, role=user.role)


@router.post("/invite-accept", response_model=UserResponse)
async def accept_invite(payload: RegisterRequest, db: AsyncSession = Depends(get_db_session)):
    return await register(payload=payload, db=db)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("50/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("100/minute", key_func=rate_limit_key_by_user)
async def login(request: Request, response: Response, payload: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    access_token, refresh_token, user, effective_role = await AuthService(db).login(
        payload.email,
        payload.password,
        tenant_id=payload.tenant_id,
        tenant_subdomain=payload.tenant_subdomain,
        request_host=request.headers.get("host"),
        device=request.headers.get("user-agent"),
        mfa_code=payload.mfa_code,
    )
    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    settings = get_settings()
    return TokenResponse(
        access_token=access_token,
        access_token_expires_in=settings.access_token_expire_minutes * 60,
        refresh_token_expires_in=settings.refresh_token_expire_minutes * 60,
        user=_serialize_user(
            user,
            tenant_id=int(decode_access_token(access_token)["tenant_id"]),
            role=effective_role,
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("120/minute", key_func=rate_limit_key_by_ip)
async def refresh_session(request: Request, response: Response, db: AsyncSession = Depends(get_db_session)):
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
    access_token, next_refresh_token, user, effective_role = await AuthService(db).refresh_session(
        refresh_token,
        device=request.headers.get("user-agent"),
    )
    _set_auth_cookies(response, access_token=access_token, refresh_token=next_refresh_token)
    settings = get_settings()
    return TokenResponse(
        access_token=access_token,
        access_token_expires_in=settings.access_token_expire_minutes * 60,
        refresh_token_expires_in=settings.refresh_token_expire_minutes * 60,
        user=_serialize_user(
            user,
            tenant_id=int(decode_access_token(access_token)["tenant_id"]),
            role=effective_role,
        ),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db_session)):
    await AuthService(db).logout(request.cookies.get(REFRESH_TOKEN_COOKIE_NAME))
    _clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/sessions", response_model=list[ActiveSessionResponse])
async def list_active_sessions(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await AuthService(db).list_active_sessions(user_id=current_user.id)


@router.post("/logout-all", response_model=AuthActionResponse)
async def logout_all_devices(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    revoked = await AuthService(db).logout_all_devices(user_id=current_user.id, tenant_id=current_user.tenant_id)
    _clear_auth_cookies(response)
    return AuthActionResponse(detail=f"Revoked {revoked} active sessions")


@router.post("/email-verification/request", response_model=AuthActionResponse)
async def request_email_verification(
    payload: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db_session),
):
    token = await AuthService(db).request_email_verification(tenant_id=payload.tenant_id, email=payload.email)
    return AuthActionResponse(detail="Email verification instructions sent", token=token)


@router.post("/email-verification/confirm", response_model=AuthActionResponse)
async def confirm_email_verification(
    payload: EmailVerificationConfirmRequest,
    db: AsyncSession = Depends(get_db_session),
):
    user = await AuthService(db).verify_email(token=payload.token)
    return AuthActionResponse(detail=f"Email verified for user {user.id}")


@router.post("/email-verification", response_model=AuthActionResponse)
async def confirm_email_verification_alias(
    payload: EmailVerificationConfirmRequest,
    db: AsyncSession = Depends(get_db_session),
):
    return await confirm_email_verification(payload=payload, db=db)


@router.post("/password-reset/request", response_model=AuthActionResponse)
async def request_password_reset(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db_session),
):
    token = await AuthService(db).request_password_reset(tenant_id=payload.tenant_id, email=payload.email)
    return AuthActionResponse(detail="Password reset instructions sent", token=token)


@router.post("/forgot-password", response_model=AuthActionResponse)
async def forgot_password(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db_session),
):
    return await request_password_reset(payload=payload, db=db)


@router.post("/password-reset/confirm", response_model=AuthActionResponse)
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db_session),
):
    user = await AuthService(db).reset_password(token=payload.token, password=payload.password)
    return AuthActionResponse(detail=f"Password reset for user {user.id}")


@router.post("/reset-password", response_model=AuthActionResponse)
async def reset_password_alias(
    payload: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db_session),
):
    return await confirm_password_reset(payload=payload, db=db)


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
    frontend_origin = settings.app_base_url.strip().rstrip("/") or next(
        (origin.strip().rstrip("/") for origin in settings.cors_origins.split(",") if origin.strip()),
        str(request.base_url).rstrip("/"),
    )
    return InviteResponse(
        invite_token=invite_token,
        invite_url=f"{frontend_origin}/auth?mode=invite&invite={invite_token}",
        email=payload.email,
        role=payload.role,
        expires_in_hours=settings.invite_token_expire_hours,
    )


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await AuthService(db).begin_mfa_setup(user_id=current_user.id, tenant_id=current_user.tenant_id)


@router.post("/mfa/enable", response_model=AuthActionResponse)
async def enable_mfa(
    payload: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    await AuthService(db).enable_mfa(user_id=current_user.id, tenant_id=current_user.tenant_id, code=payload.code)
    return AuthActionResponse(detail="Multi-factor authentication enabled")


@router.post("/mfa/disable", response_model=AuthActionResponse)
async def disable_mfa(
    payload: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    await AuthService(db).disable_mfa(user_id=current_user.id, tenant_id=current_user.tenant_id, code=payload.code)
    return AuthActionResponse(detail="Multi-factor authentication disabled")
