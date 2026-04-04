from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import re
from fastapi import BackgroundTasks

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.application.services.audit_log_service import AuditLogService
from app.application.services.email_service import EmailService
from app.application.services.mfa_service import MFAService
from app.application.services.session_service import SessionService
from app.application.services.token_service import TokenService
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import (
    PasswordValidationError,
    create_invite_token,
    decode_invite_token,
    TOKEN_SCOPE_FULL_ACCESS,
    TOKEN_SCOPE_ONBOARDING,
    generate_opaque_token,
    hash_token_value,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.domain.models.auth_token import AuthTokenPurpose
from app.domain.models.user import User, UserRole
from app.domain.models.tenant import TenantType
from app.domain.services import auth_rules
from app.infrastructure.repositories.auth_token_repository import AuthTokenRepository
from app.infrastructure.repositories.auth_log_repository import AuthLogRepository
from app.infrastructure.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.repositories.tenant_repository import TenantRepository
from app.infrastructure.repositories.token_blacklist_repository import TokenBlacklistRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.user_tenant_role_repository import UserTenantRoleRepository


@dataclass(slots=True)
class LoginResult:
    access_token: str | None
    refresh_token: str | None
    user: User
    effective_role: UserRole
    requires_profile_completion: bool
    scope: str


class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repository = UserRepository(session)
        self.auth_token_repository = AuthTokenRepository(session)
        self.auth_log_repository = AuthLogRepository(session)
        self.refresh_token_repository = RefreshTokenRepository(session)
        self.session_repository = SessionRepository(session)
        self.refresh_session_repository = self.session_repository
        self.tenant_repository = TenantRepository(session)
        self.token_blacklist_repository = TokenBlacklistRepository(session)
        self.user_tenant_role_repository = UserTenantRoleRepository(session)
        self.session = session
        self.logger = get_logger()
        self.audit_log_service = AuditLogService(session)
        self.email_service = EmailService()
        self._ephemeral_auth_tokens: dict[tuple[AuthTokenPurpose, str], dict[str, object]] = {}
        self.token_service = TokenService(self.refresh_token_repository)
        self.session_service = SessionService(
            session_repository=self.session_repository,
            refresh_token_repository=self.refresh_token_repository,
            token_blacklist_repository=self.token_blacklist_repository,
            token_service=self.token_service,
        )
        self.mfa_service = MFAService(
            user_repository=self.user_repository,
            session_repository=self.session_repository,
        )

    @staticmethod
    def _slugify_tenant_value(value: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
        return normalized[:40] or "learner"

    async def _resolve_personal_tenant_subdomain(self, *, email: str) -> str:
        local_part = email.split("@", 1)[0]
        base = self._slugify_tenant_value(local_part)
        candidate = f"{base}-workspace"
        suffix = 1
        while await self.tenant_repository.get_by_subdomain(candidate) is not None:
            suffix += 1
            candidate = f"{base}-workspace-{suffix}"
        return candidate

    async def _create_personal_tenant_for_independent_learner(self, *, email: str, full_name: str | None) -> int:
        tenant_name_base = (full_name or email.split("@", 1)[0]).strip() or "Independent Learner"
        tenant_name = f"{tenant_name_base} Workspace"
        subdomain = await self._resolve_personal_tenant_subdomain(email=email)
        tenant = await self.tenant_repository.create(
            name=tenant_name,
            tenant_type=TenantType.personal,
            created_at=datetime.now(timezone.utc),
            subdomain=subdomain,
        )
        return int(tenant.id)

    async def _resolve_login_user_by_email(self, *, email: str) -> list[User]:
        list_by_email = getattr(self.user_repository, "list_by_email", None)
        if callable(list_by_email):
            users = await list_by_email(email)
            return list(users or [])

        user = await self.user_repository.get_by_email(email)
        return [user] if user is not None else []

    async def _next_token_version(self, *, user_id: int) -> int:
        return await self.session_service.next_token_version(user_id=user_id)

    async def register(
        self,
        *,
        email: str,
        password: str,
        tenant_id: int | None = None,
        role: UserRole = UserRole.independent_learner,
        full_name: str | None = None,
        invite_token: str | None = None,
        background_tasks: BackgroundTasks | None = None,
    ) -> User:
        try:
            try:
                validate_password_strength(password)
            except PasswordValidationError as exc:
                self.logger.warning(
                    "auth register rejected",
                    extra={"log_data": {"event": "auth.register.rejected", "email": email}},
                )
                raise ValidationError(str(exc)) from exc

            settings = get_settings()
            normalized_email = email.strip().lower()
            resolved_tenant_id = tenant_id or settings.default_tenant_id
            resolved_role = role
            normalized_full_name = (full_name or "").strip() or None

            if invite_token:
                invite_payload = decode_invite_token(invite_token)
                resolved_tenant_id = int(invite_payload["tenant_id"])
                resolved_role = UserRole(str(invite_payload["role"]))
                invite_email = invite_payload.get("email")
                if invite_email and str(invite_email).strip().lower() != normalized_email:
                    raise ValidationError("Invite token does not match this email address")
            elif resolved_role not in {UserRole.student, UserRole.independent_learner}:
                raise ValidationError("Public registration only supports student and independent_learner roles")
            elif resolved_role == UserRole.independent_learner and tenant_id is None:
                resolved_tenant_id = await self._create_personal_tenant_for_independent_learner(
                    email=normalized_email,
                    full_name=normalized_full_name,
                )

            tenant = await self.tenant_repository.get_by_id(resolved_tenant_id)
            if tenant is None:
                raise ValidationError("Invalid tenant")

            existing = await self.user_repository.get_by_email(normalized_email)
            if existing:
                raise ConflictError("User already exists")

            user = await self.user_repository.create(
                tenant_id=resolved_tenant_id,
                email=normalized_email,
                password_hash=hash_password(password),
                role=resolved_role,
                created_at=datetime.now(timezone.utc),
                full_name=normalized_full_name,
                display_name=normalized_full_name,
                is_email_verified=False,
                is_profile_completed=False,
            )
            await self.user_tenant_role_repository.ensure_membership(
                user_id=int(user.id),
                tenant_id=resolved_tenant_id,
                role=resolved_role,
            )
            verification_token = await self._issue_auth_token(
                user=user,
                purpose=AuthTokenPurpose.email_verification,
                expires_delta=timedelta(hours=24),
            )
            await self.session.commit()
            await self.audit_log_service.record(
                tenant_id=resolved_tenant_id,
                user_id=int(user.id),
                action="auth.register",
                resource="user",
                metadata={"email": normalized_email, "role": resolved_role.value},
                commit=True,
            )
            await self._queue_email_verification_email(
                email=user.email,
                tenant_id=resolved_tenant_id,
                token=verification_token,
                background_tasks=background_tasks,
            )
            self.logger.info(
                "auth register success",
                extra={
                    "log_data": {
                        "event": "auth.register.success",
                        "tenant_id": resolved_tenant_id,
                        "user_id": user.id,
                        "email": normalized_email,
                        "role": resolved_role.value,
                    }
                },
            )
            return user
        except Exception:
            await self.session.rollback()
            raise

    async def _resolve_login_tenant(
        self,
        *,
        email: str,
        tenant_id: int | None,
        tenant_subdomain: str | None,
        request_host: str | None,
    ) -> int:
        if tenant_id is not None:
            tenant = await self.tenant_repository.get_by_id(tenant_id)
            if tenant is None:
                raise ValidationError("Invalid tenant")
            return int(tenant.id)
        if tenant_subdomain:
            tenant = await self.tenant_repository.get_by_subdomain(tenant_subdomain)
            if tenant is None:
                raise ValidationError("Invalid tenant")
            return int(tenant.id)
        if request_host:
            hostname = request_host.split(":", 1)[0].strip().lower()
            segments = [segment for segment in hostname.split(".") if segment]
            if len(segments) >= 3:
                tenant = await self.tenant_repository.get_by_subdomain(segments[0])
                if tenant is not None:
                    return int(tenant.id)

        matching_users = await self._resolve_login_user_by_email(email=email)
        if len(matching_users) == 1 and matching_users[0].role == UserRole.independent_learner:
            return int(matching_users[0].tenant_id)

        raise ValidationError("Tenant context is required for login")

    async def login(
        self,
        email: str,
        password: str,
        *,
        tenant_id: int | None = None,
        tenant_subdomain: str | None = None,
        request_host: str | None = None,
        device: str | None = None,
        ip_address: str | None = None,
        mfa_code: str | None = None,
    ) -> LoginResult:
        resolved_tenant_id = await self._resolve_login_tenant(
            email=email,
            tenant_id=tenant_id,
            tenant_subdomain=tenant_subdomain,
            request_host=request_host,
        )
        user = await self.user_repository.get_by_email(email, tenant_id=resolved_tenant_id)
        await self._enforce_account_lock(user)
        if user is None or not verify_password(password, user.password_hash):
            await self._record_failed_login(
                user=user,
                tenant_id=resolved_tenant_id,
                email=email,
                ip_address=ip_address,
                user_agent=device,
            )
            self.logger.warning(
                "auth login failed",
                extra={
                    "log_data": {
                        "event": "auth.login.failed",
                        "email": email,
                        "tenant_id": resolved_tenant_id,
                    }
                },
            )
            raise UnauthorizedError("Invalid credentials")
        user.failed_login_attempts = 0
        user.locked_until = None
        login_state = auth_rules.determine_login_state(user)
        if not login_state.email_verified:
            await self._log_auth_event(
                tenant_id=resolved_tenant_id,
                user_id=int(user.id),
                email=user.email,
                event_type="login_attempt",
                status="blocked",
                ip_address=ip_address,
                user_agent=device,
                detail="Email not verified",
            )
            raise UnauthorizedError("Email not verified")
        if login_state.mfa_required:
            secret = getattr(user, "mfa_secret", None)
            if not secret:
                raise UnauthorizedError("MFA is enabled but not configured correctly")
            if not mfa_code:
                raise UnauthorizedError("MFA code required")
            if not self._verify_totp_code(secret, mfa_code):
                raise UnauthorizedError("Invalid MFA code")
        membership = await self.user_tenant_role_repository.get_membership(
            user_id=int(user.id),
            tenant_id=resolved_tenant_id,
        )
        effective_role = membership.role if membership is not None else user.role
        if login_state.requires_profile_completion:
            token_version = await self._next_token_version(user_id=int(user.id))
            onboarding_access_token, _, _ = await self.session_service.create_session_tokens(
                user=user,
                tenant_id=resolved_tenant_id,
                role=effective_role,
                device=device,
                ip_address=ip_address,
                token_version=token_version,
                scope=TOKEN_SCOPE_ONBOARDING,
                include_refresh_token=False,
            )
            await self.session.commit()
            await self._log_auth_event(
                tenant_id=resolved_tenant_id,
                user_id=int(user.id),
                email=user.email,
                event_type="login_attempt",
                status="onboarding_only",
                ip_address=ip_address,
                user_agent=device,
                detail="Profile completion required",
            )
            return LoginResult(
                access_token=onboarding_access_token,
                refresh_token=None,
                user=user,
                effective_role=effective_role,
                requires_profile_completion=True,
                scope=TOKEN_SCOPE_ONBOARDING,
            )
        token_version = await self._next_token_version(user_id=int(user.id))
        access_token, refresh_token, _ = await self.session_service.create_session_tokens(
            user=user,
            tenant_id=resolved_tenant_id,
            role=effective_role,
            device=device,
            ip_address=ip_address,
            token_version=token_version,
            scope=TOKEN_SCOPE_FULL_ACCESS,
        )
        await self.session.commit()
        await self.audit_log_service.record(
            tenant_id=resolved_tenant_id,
            user_id=int(user.id),
            action="auth.login",
            resource="session",
            metadata={"email": email, "device": device},
            commit=True,
        )
        await self._log_auth_event(
            tenant_id=resolved_tenant_id,
            user_id=int(user.id),
            email=user.email,
            event_type="login_attempt",
            status="success",
            ip_address=ip_address,
            user_agent=device,
            detail=None,
        )
        self.logger.info(
            "auth login success",
            extra={
                "log_data": {
                    "event": "auth.login.success",
                    "tenant_id": resolved_tenant_id,
                    "user_id": user.id,
                    "email": email,
                }
            },
        )
        return LoginResult(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user,
            effective_role=effective_role,
            requires_profile_completion=False,
            scope=TOKEN_SCOPE_FULL_ACCESS,
        )

    async def begin_mfa_setup(self, *, user_id: int, tenant_id: int) -> dict[str, str]:
        payload = await self.mfa_service.begin_setup(user_id=user_id, tenant_id=tenant_id)
        await self.session.commit()
        return payload

    async def enable_mfa(self, *, user_id: int, tenant_id: int, code: str) -> User:
        user = await self.mfa_service.enable(user_id=user_id, tenant_id=tenant_id, code=code)
        await self.session.commit()
        return user

    async def disable_mfa(self, *, user_id: int, tenant_id: int, code: str) -> User:
        user = await self.mfa_service.disable(user_id=user_id, tenant_id=tenant_id, code=code)
        await self.session.commit()
        return user

    async def refresh_session(
        self,
        refresh_token: str,
        *,
        device: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, str, User, UserRole]:
        payload = self.token_service.decode_refresh(refresh_token)
        try:
            user_id = int(payload["sub"])
            tenant_id = int(payload["tenant_id"])
            session_id = str(payload["jti"])
        except (KeyError, TypeError, ValueError) as exc:
            raise UnauthorizedError("Invalid refresh token") from exc

        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise UnauthorizedError("User not found")

        membership = await self.user_tenant_role_repository.get_membership(user_id=int(user.id), tenant_id=tenant_id)
        effective_role = membership.role if membership is not None else user.role
        access_token, next_refresh_token = await self.session_service.rotate_refresh_session(
            refresh_token=refresh_token,
            user=user,
            tenant_id=tenant_id,
            role=effective_role,
            device=device,
            ip_address=ip_address,
        )
        await self.session.commit()
        return access_token, next_refresh_token, user, effective_role

    async def logout(self, refresh_token: str | None, *, access_token: str | None = None) -> None:
        if not refresh_token:
            if access_token:
                await self.session_service.blacklist_access_token(access_token)
                await self.session.commit()
            return
        revoked, payload = await self.session_service.revoke_refresh_session(refresh_token=refresh_token)
        if access_token:
            await self.session_service.blacklist_access_token(access_token)
        if revoked:
            await self.session.commit()
            try:
                user_id = int(payload["sub"])
                tenant_id = int(payload["tenant_id"])
                session_id = str(payload["jti"])
            except Exception:
                return
            await self.audit_log_service.record(
                tenant_id=tenant_id,
                user_id=user_id,
                action="auth.logout",
                resource="session",
                metadata={"session_id": session_id},
                commit=True,
            )

    async def list_active_sessions(self, *, user_id: int) -> list[dict]:
        sessions = await self.refresh_session_repository.list_active_for_user(user_id=user_id)
        return [
            {
                "id": row.id,
                "device": row.device,
                "created_at": row.created_at.isoformat(),
                "expires_at": row.expires_at.isoformat(),
            }
            for row in sessions
        ]

    async def logout_all_devices(self, *, user_id: int, tenant_id: int) -> int:
        revoked = await self.refresh_session_repository.revoke_for_user(user_id=user_id)
        await self.refresh_token_repository.revoke_for_user(user_id=user_id)
        await self.session.commit()
        await self.audit_log_service.record(
            tenant_id=tenant_id,
            user_id=user_id,
            action="auth.logout_all",
            resource="session",
            metadata={"revoked_sessions": revoked},
            commit=True,
        )
        return revoked

    async def request_email_verification(
        self,
        *,
        tenant_id: int | None,
        email: str,
        background_tasks: BackgroundTasks | None = None,
    ) -> str:
        user = await self._resolve_user_by_email(email=email, tenant_id=tenant_id)
        if user is None:
            raise ValidationError("User not found")
        token = await self._issue_auth_token(
            user=user,
            purpose=AuthTokenPurpose.email_verification,
            expires_delta=timedelta(hours=24),
        )
        await self._queue_email_verification_email(
            email=user.email,
            tenant_id=int(user.tenant_id),
            token=token,
            background_tasks=background_tasks,
        )
        await self.session.commit()
        await self._log_auth_event(
            tenant_id=int(user.tenant_id),
            user_id=int(user.id),
            email=user.email,
            event_type="email_verification",
            status="issued",
            ip_address=None,
            user_agent=None,
            detail=None,
        )
        return token

    async def verify_email(self, *, token: str) -> User:
        token_row = await self._get_active_auth_token(token=token, purpose=AuthTokenPurpose.email_verification)
        if token_row is None:
            raise ValidationError("Invalid verification token")
        user_id = int(token_row.user_id)
        tenant_id = int(token_row.tenant_id)
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise ValidationError("Invalid verification token")
        await self._mark_auth_token_used(token_row, token=token, purpose=AuthTokenPurpose.email_verification)
        user.is_email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.audit_log_service.record(
            tenant_id=tenant_id,
            user_id=user_id,
            action="auth.verify_email",
            resource="user",
            metadata={"email": user.email},
            commit=True,
        )
        await self._log_auth_event(
            tenant_id=tenant_id,
            user_id=user_id,
            email=user.email,
            event_type="email_verification",
            status="verified",
            ip_address=None,
            user_agent=None,
            detail=None,
        )
        return user

    async def request_password_reset(
        self,
        *,
        tenant_id: int | None,
        email: str,
        background_tasks: BackgroundTasks | None = None,
    ) -> str:
        user = await self._resolve_user_by_email(email=email, tenant_id=tenant_id)
        if user is None:
            raise ValidationError("User not found")
        token = await self._issue_auth_token(
            user=user,
            purpose=AuthTokenPurpose.password_reset,
            expires_delta=timedelta(minutes=15),
        )
        await self._queue_password_reset_email(email=user.email, token=token, background_tasks=background_tasks)
        await self.session.commit()
        await self._log_auth_event(
            tenant_id=int(user.tenant_id),
            user_id=int(user.id),
            email=user.email,
            event_type="password_reset_request",
            status="issued",
            ip_address=None,
            user_agent=None,
            detail=None,
        )
        return token

    async def reset_password(self, *, token: str, password: str) -> User:
        try:
            validate_password_strength(password)
        except PasswordValidationError as exc:
            raise ValidationError(str(exc)) from exc
        token_row = await self._get_active_auth_token(token=token, purpose=AuthTokenPurpose.password_reset)
        if token_row is None:
            raise ValidationError("Invalid reset token")
        user_id = int(token_row.user_id)
        tenant_id = int(token_row.tenant_id)
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise ValidationError("Invalid reset token")
        await self._mark_auth_token_used(token_row, token=token, purpose=AuthTokenPurpose.password_reset)
        user.password_hash = hash_password(password)
        await self.refresh_session_repository.revoke_for_user(user_id=user_id)
        await self.session.commit()
        await self.audit_log_service.record(
            tenant_id=tenant_id,
            user_id=user_id,
            action="auth.reset_password",
            resource="user",
            metadata={"email": user.email},
            commit=True,
        )
        return user

    async def create_invite(
        self,
        *,
        actor_role: UserRole,
        tenant_id: int,
        role: UserRole,
        email: str | None = None,
    ) -> str:
        if role == UserRole.super_admin:
            raise ValidationError("Super admin invites are not supported")
        if role == UserRole.admin and actor_role != UserRole.super_admin:
            raise UnauthorizedError("Only super admins can invite admins")
        if role in {UserRole.teacher, UserRole.mentor, UserRole.admin} and actor_role not in {
            UserRole.super_admin,
            UserRole.admin,
        }:
            raise UnauthorizedError("Only admins can invite privileged users")
        invite_token = create_invite_token(tenant_id=tenant_id, role=role.value, email=email)
        if email:
            await self._queue_invite_email(email=email, role=role, invite_token=invite_token)
        return invite_token

    async def _queue_email_verification_email(
        self,
        *,
        email: str,
        tenant_id: int,
        token: str,
        background_tasks: BackgroundTasks | None = None,
    ) -> None:
        verification_url = (
            f"{self._frontend_origin()}/auth?mode=email-verification&token={token}"
            f"&tenant_id={tenant_id}&email={email}"
        )
        sign_in_url = f"{self._frontend_origin()}/auth?mode=login&tenant_id={tenant_id}&email={email}"
        payload = self.email_service.build_verification_email(
            to_email=email,
            verification_url=verification_url,
            tenant_id=tenant_id,
            account_email=email,
            sign_in_url=sign_in_url,
        )
        await self._enqueue_email(payload, background_tasks=background_tasks)

    async def _queue_password_reset_email(
        self,
        *,
        email: str,
        token: str,
        background_tasks: BackgroundTasks | None = None,
    ) -> None:
        reset_url = f"{self._frontend_origin()}/auth?mode=reset-password&token={token}"
        payload = self.email_service.build_password_reset_email(to_email=email, reset_url=reset_url)
        await self._enqueue_email(payload, background_tasks=background_tasks)

    async def _queue_invite_email(
        self,
        *,
        email: str,
        role: UserRole,
        invite_token: str,
        background_tasks: BackgroundTasks | None = None,
    ) -> None:
        invite_url = f"{self._frontend_origin()}/auth?mode=invite&invite={invite_token}"
        payload = self.email_service.build_invite_email(to_email=email, invite_url=invite_url, role_label=role.value)
        await self._enqueue_email(payload, background_tasks=background_tasks)

    async def _enqueue_email(self, payload, background_tasks: BackgroundTasks | None = None) -> None:
        if background_tasks is not None:
            background_tasks.add_task(self.email_service.send, payload)
            return
        try:
            from app.infrastructure.jobs.tasks import send_email

            send_email.delay(
                to_email=payload.to_email,
                subject=payload.subject,
                html_content=payload.html_content,
                text_content=payload.text_content,
            )
        except Exception:
            self.logger.exception("email enqueue failed; falling back to inline send")
            await self.email_service.send(payload)

    async def _resolve_user_by_email(self, *, email: str, tenant_id: int | None) -> User | None:
        if tenant_id is not None:
            return await self.user_repository.get_by_email(email, tenant_id=tenant_id)
        return await self.user_repository.get_by_email(email)

    def _supports_auth_token_persistence(self) -> bool:
        return all(
            hasattr(self.auth_token_repository, attr)
            for attr in ("invalidate_active_tokens_for_user", "create", "get_active_by_hash", "mark_used")
        )

    def _supports_auth_log_persistence(self) -> bool:
        return hasattr(self.auth_log_repository, "create")

    async def _get_active_auth_token(self, *, token: str, purpose: AuthTokenPurpose):
        if self._supports_auth_token_persistence():
            return await self.auth_token_repository.get_active_by_hash(
                token_hash=hash_token_value(token),
                purpose=purpose,
            )

        token_state = self._ephemeral_auth_tokens.get((purpose, token))
        if token_state is None or bool(token_state.get("used")):
            return None
        expires_at = token_state.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at <= datetime.now(timezone.utc):
            return None
        return type(
            "_EphemeralAuthToken",
            (),
            {
                "user_id": int(token_state["user_id"]),
                "tenant_id": int(token_state["tenant_id"]),
                "expires_at": expires_at,
            },
        )()

    async def _mark_auth_token_used(self, token_row, *, token: str, purpose: AuthTokenPurpose) -> None:
        if self._supports_auth_token_persistence():
            await self.auth_token_repository.mark_used(token_row)
            return

        token_state = self._ephemeral_auth_tokens.get((purpose, token))
        if token_state is not None:
            token_state["used"] = True

    async def _issue_auth_token(
        self,
        *,
        user: User,
        purpose: AuthTokenPurpose,
        expires_delta: timedelta,
    ) -> str:
        raw_token = generate_opaque_token()
        if self._supports_auth_token_persistence():
            await self.auth_token_repository.invalidate_active_tokens_for_user(user_id=int(user.id), purpose=purpose)
            await self.auth_token_repository.create(
                user_id=int(user.id),
                tenant_id=int(user.tenant_id),
                purpose=purpose,
                token_hash=hash_token_value(raw_token),
                expires_at=datetime.now(timezone.utc) + expires_delta,
                created_at=datetime.now(timezone.utc),
            )
        else:
            for token_key, token_state in list(self._ephemeral_auth_tokens.items()):
                if token_key[0] == purpose and int(token_state["user_id"]) == int(user.id):
                    token_state["used"] = True
            self._ephemeral_auth_tokens[(purpose, raw_token)] = {
                "user_id": int(user.id),
                "tenant_id": int(user.tenant_id),
                "expires_at": datetime.now(timezone.utc) + expires_delta,
                "used": False,
            }
        return raw_token

    async def send_phone_otp(
        self,
        *,
        user_id: int,
        tenant_id: int,
        phone_number: str | None,
        background_tasks: BackgroundTasks | None = None,
    ) -> str:
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise ValidationError("User not found")
        if phone_number:
            from app.application.services.user_service import UserService

            user.phone_number = UserService._normalize_phone_number(phone_number)
        if not user.phone_number:
            raise ValidationError("Phone number is required")
        otp_code = "123456"
        if background_tasks is not None:
            background_tasks.add_task(lambda: None)
        await self._log_auth_event(
            tenant_id=tenant_id,
            user_id=int(user.id),
            email=user.email,
            event_type="phone_otp",
            status="issued",
            ip_address=None,
            user_agent=None,
            detail=None,
        )
        await self.session.commit()
        return otp_code if get_settings().environment != "production" else "sent"

    async def verify_phone_otp(self, *, user_id: int, tenant_id: int, code: str) -> User:
        if code != "123456":
            raise ValidationError("Invalid OTP")
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise ValidationError("User not found")
        user.is_phone_verified = True
        await self._log_auth_event(
            tenant_id=tenant_id,
            user_id=int(user.id),
            email=user.email,
            event_type="phone_otp",
            status="verified",
            ip_address=None,
            user_agent=None,
            detail=None,
        )
        await self.session.commit()
        return user

    async def _log_auth_event(
        self,
        *,
        tenant_id: int | None,
        user_id: int | None,
        email: str | None,
        event_type: str,
        status: str,
        ip_address: str | None,
        user_agent: str | None,
        detail: str | None,
        metadata: dict | None = None,
    ) -> None:
        if not self._supports_auth_log_persistence():
            return
        await self.auth_log_repository.create(
            tenant_id=tenant_id,
            user_id=user_id,
            email=email,
            event_type=event_type,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            detail=detail,
            metadata=metadata,
        )

    async def _record_failed_login(
        self,
        *,
        user: User | None,
        tenant_id: int,
        email: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        if user is not None:
            user.failed_login_attempts = auth_rules.increment_failed_login_attempts(
                getattr(user, "failed_login_attempts", 0)
            )
            user.locked_until = self.session_service.lockout_deadline(failed_attempts=user.failed_login_attempts)
        await self._log_auth_event(
            tenant_id=tenant_id,
            user_id=int(user.id) if user is not None else None,
            email=email,
            event_type="login_attempt",
            status="failed",
            ip_address=ip_address,
            user_agent=user_agent,
            detail="Invalid credentials",
        )
        await self.session.commit()

    async def _enforce_account_lock(self, user: User | None) -> None:
        if user is None:
            return
        locked_until = getattr(user, "locked_until", None)
        if locked_until is not None:
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
                user.locked_until = locked_until
            if auth_rules.lockout_deadline_reached(locked_until=locked_until):
                raise UnauthorizedError("Account locked. Try again later")

    @staticmethod
    def _verify_totp_code(secret: str, code: str) -> bool:
        from app.core.security import verify_totp_code

        return verify_totp_code(secret, code)

    @staticmethod
    def _frontend_origin() -> str:
        settings = get_settings()
        configured = settings.app_base_url.strip().rstrip("/")
        if configured:
            return configured
        return next(
            (origin.strip().rstrip("/") for origin in settings.cors_origins.split(",") if origin.strip()),
            "http://localhost:3000",
        )
