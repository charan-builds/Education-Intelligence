from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
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
    LogoutRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    OTPRequest,
    OTPVerifyRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user_schema import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(db)


def _serialize_user(user, *, tenant_id: int, role) -> UserResponse:
    return UserResponse.model_validate(
        {
            "id": int(user.id),
            "tenant_id": tenant_id,
            "email": user.email,
            "role": role,
            "full_name": getattr(user, "full_name", None),
            "display_name": getattr(user, "display_name", None),
            "phone_number": getattr(user, "phone_number", None),
            "linkedin_url": getattr(user, "linkedin_url", None),
            "organization_name": getattr(user, "college_name", None),
            "college_name": getattr(user, "college_name", None),
            "avatar_url": getattr(user, "avatar_url", None),
            "preferences": getattr(user, "preferences_json", None) or {},
            "mfa_enabled": bool(getattr(user, "mfa_enabled", False)),
            "is_email_verified": bool(getattr(user, "is_email_verified", False) or getattr(user, "email_verified_at", None)),
            "is_phone_verified": bool(getattr(user, "is_phone_verified", False)),
            "email_verified_at": getattr(user, "email_verified_at", None),
            "is_profile_completed": bool(getattr(user, "is_profile_completed", False)),
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
async def register(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(get_auth_service),
):
    user = await service.register(
        email=payload.email,
        password=payload.password,
        tenant_id=payload.tenant_id,
        role=payload.role,
        full_name=payload.full_name,
        invite_token=payload.invite_token,
        background_tasks=background_tasks,
    )
    tenant_id = int(payload.tenant_id) if getattr(payload, "tenant_id", None) is not None else int(user.tenant_id)
    return _serialize_user(user, tenant_id=tenant_id, role=user.role)


@router.post("/invite-accept", response_model=UserResponse)
async def accept_invite(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(get_auth_service),
):
    return await register(payload=payload, background_tasks=background_tasks, service=service)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute", key_func=rate_limit_key_by_ip)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
    service: AuthService = Depends(get_auth_service),
):
    resolved_service = service if hasattr(service, "login") else AuthService(db)
    result = await resolved_service.login(
        payload.email,
        payload.password,
        tenant_id=payload.tenant_id,
        tenant_subdomain=payload.tenant_subdomain,
        request_host=request.headers.get("host"),
        device=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
        mfa_code=payload.mfa_code,
    )
    if result.access_token and result.refresh_token:
        _set_auth_cookies(response, access_token=result.access_token, refresh_token=result.refresh_token)
    settings = get_settings()
    return TokenResponse(
        authenticated=not result.requires_profile_completion,
        requires_profile_completion=result.requires_profile_completion,
        scope=result.scope,
        access_token=result.access_token,
        access_token_expires_in=settings.access_token_expire_minutes * 60 if result.access_token else None,
        refresh_token_expires_in=settings.refresh_token_expire_minutes * 60 if result.refresh_token else None,
        user=_serialize_user(
            result.user,
            tenant_id=int(result.user.tenant_id if result.requires_profile_completion else decode_access_token(result.access_token)["tenant_id"]),
            role=result.effective_role,
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("120/minute", key_func=rate_limit_key_by_ip)
async def refresh_session(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: AsyncSession = Depends(get_db_session),
    service: AuthService = Depends(get_auth_service),
):
    resolved_service = service if hasattr(service, "refresh_session") else AuthService(db)
    refresh_token = (payload.refresh_token if payload else None) or request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
    access_token, next_refresh_token, user, effective_role = await resolved_service.refresh_session(
        refresh_token,
        device=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_auth_cookies(response, access_token=access_token, refresh_token=next_refresh_token)
    settings = get_settings()
    return TokenResponse(
        access_token=access_token,
        access_token_expires_in=settings.access_token_expire_minutes * 60,
        refresh_token_expires_in=settings.refresh_token_expire_minutes * 60,
        scope="full_access",
        user=_serialize_user(
            user,
            tenant_id=int(decode_access_token(access_token)["tenant_id"]),
            role=effective_role,
        ),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    payload: LogoutRequest | None = None,
    db: AsyncSession = Depends(get_db_session),
    service: AuthService = Depends(get_auth_service),
):
    resolved_service = service if hasattr(service, "logout") else AuthService(db)
    refresh_token = (payload.refresh_token if payload else None) or request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if access_token is None:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            access_token = auth_header.split(" ", 1)[1].strip()
    await resolved_service.logout(refresh_token, access_token=access_token)
    _clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/sessions", response_model=list[ActiveSessionResponse])
async def list_active_sessions(
    service: AuthService = Depends(get_auth_service),
    current_user=Depends(get_current_user),
):
    return await service.list_active_sessions(user_id=current_user.id)


@router.post("/logout-all", response_model=AuthActionResponse)
async def logout_all_devices(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    current_user=Depends(get_current_user),
):
    revoked = await service.logout_all_devices(user_id=current_user.id, tenant_id=current_user.tenant_id)
    _clear_auth_cookies(response)
    return AuthActionResponse(detail=f"Revoked {revoked} active sessions")


@router.post("/email-verification/request", response_model=AuthActionResponse)
async def request_email_verification(
    payload: EmailVerificationRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(get_auth_service),
):
    token = await service.request_email_verification(
        tenant_id=payload.tenant_id,
        email=payload.email,
        background_tasks=background_tasks,
    )
    return AuthActionResponse(detail="Email verification instructions sent", token=token)


@router.post("/email-verification/confirm", response_model=AuthActionResponse)
async def confirm_email_verification(
    payload: EmailVerificationConfirmRequest,
    service: AuthService = Depends(get_auth_service),
):
    user = await service.verify_email(token=payload.token)
    return AuthActionResponse(detail=f"Email verified for user {user.id}")


@router.post("/email-verification", response_model=AuthActionResponse)
async def confirm_email_verification_alias(
    payload: EmailVerificationConfirmRequest,
    service: AuthService = Depends(get_auth_service),
):
    user = await service.verify_email(token=payload.token)
    return AuthActionResponse(detail=f"Email verified for user {user.id}")


@router.post("/verify-email", response_model=AuthActionResponse)
async def verify_email_alias(
    payload: EmailVerificationConfirmRequest,
    service: AuthService = Depends(get_auth_service),
):
    user = await service.verify_email(token=payload.token)
    return AuthActionResponse(detail=f"Email verified for user {user.id}")


@router.post("/password-reset/request", response_model=AuthActionResponse)
async def request_password_reset(
    payload: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(get_auth_service),
):
    token = await service.request_password_reset(
        tenant_id=payload.tenant_id,
        email=payload.email,
        background_tasks=background_tasks,
    )
    return AuthActionResponse(detail="Password reset instructions sent", token=token)


@router.post("/forgot-password", response_model=AuthActionResponse)
@limiter.limit("3/minute", key_func=rate_limit_key_by_ip)
async def forgot_password(
    request: Request,
    payload: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    return await request_password_reset(payload=payload, background_tasks=background_tasks, db=db)


@router.post("/send-otp", response_model=AuthActionResponse)
async def send_phone_otp(
    payload: OTPRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(get_auth_service),
    current_user=Depends(get_current_user),
):
    code = await service.send_phone_otp(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        phone_number=payload.phone_number,
        background_tasks=background_tasks,
    )
    return AuthActionResponse(detail="OTP sent", token=code)


@router.post("/verify-otp", response_model=AuthActionResponse)
async def verify_phone_otp(
    payload: OTPVerifyRequest,
    service: AuthService = Depends(get_auth_service),
    current_user=Depends(get_current_user),
):
    await service.verify_phone_otp(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        code=payload.code,
    )
    return AuthActionResponse(detail="Phone verified")


@router.post("/password-reset/confirm", response_model=AuthActionResponse)
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    service: AuthService = Depends(get_auth_service),
):
    user = await service.reset_password(token=payload.token, password=payload.password)
    return AuthActionResponse(detail=f"Password reset for user {user.id}")


@router.post("/reset-password", response_model=AuthActionResponse)
async def reset_password_alias(
    payload: PasswordResetConfirmRequest,
    service: AuthService = Depends(get_auth_service),
):
    user = await service.reset_password(token=payload.token, password=payload.password)
    return AuthActionResponse(detail=f"Password reset for user {user.id}")


@router.post("/invites", response_model=InviteResponse)
async def create_invite(
    payload: InviteCreateRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    current_user=Depends(require_roles("super_admin", "admin")),
):
    invite_token = await service.create_invite(
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
    service: AuthService = Depends(get_auth_service),
    current_user=Depends(get_current_user),
):
    return await service.begin_mfa_setup(user_id=current_user.id, tenant_id=current_user.tenant_id)


@router.post("/mfa/enable", response_model=AuthActionResponse)
async def enable_mfa(
    payload: MFAVerifyRequest,
    service: AuthService = Depends(get_auth_service),
    current_user=Depends(get_current_user),
):
    await service.enable_mfa(user_id=current_user.id, tenant_id=current_user.tenant_id, code=payload.code)
    return AuthActionResponse(detail="Multi-factor authentication enabled")


@router.post("/mfa/disable", response_model=AuthActionResponse)
async def disable_mfa(
    payload: MFAVerifyRequest,
    service: AuthService = Depends(get_auth_service),
    current_user=Depends(get_current_user),
):
    await service.disable_mfa(user_id=current_user.id, tenant_id=current_user.tenant_id, code=payload.code)
    return AuthActionResponse(detail="Multi-factor authentication disabled")
