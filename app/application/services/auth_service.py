from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.application.services.audit_log_service import AuditLogService
from app.application.services.email_service import EmailService
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import (
    PasswordValidationError,
    build_totp_uri,
    create_access_token,
    create_email_verification_token,
    create_invite_token,
    create_password_reset_token,
    create_refresh_token_with_jti,
    decode_email_verification_token,
    decode_invite_token,
    decode_password_reset_token,
    decode_refresh_token,
    generate_totp_secret,
    hash_password,
    validate_password_strength,
    verify_totp_code,
    verify_password,
)
from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.repositories.tenant_repository import TenantRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.user_tenant_role_repository import UserTenantRoleRepository


class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repository = UserRepository(session)
        self.session_repository = SessionRepository(session)
        self.refresh_session_repository = self.session_repository
        self.tenant_repository = TenantRepository(session)
        self.user_tenant_role_repository = UserTenantRoleRepository(session)
        self.session = session
        self.logger = get_logger()
        self.audit_log_service = AuditLogService(session)
        self.email_service = EmailService()

    @staticmethod
    def _refresh_session_expiry() -> datetime:
        settings = get_settings()
        return datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes)

    async def _next_token_version(self, *, user_id: int) -> int:
        repository = self.refresh_session_repository
        if hasattr(repository, "next_token_version_for_user"):
            return await repository.next_token_version_for_user(user_id=user_id)
        try:
            return await self.session_repository.next_token_version_for_user(user_id=user_id)
        except AttributeError:
            return 1

    async def _create_refresh_session(
        self,
        *,
        user: User,
        tenant_id: int,
        role: UserRole,
        device: str | None,
        token_version: int | None = None,
    ) -> str:
        session_id = uuid4().hex
        resolved_token_version = token_version or await self._next_token_version(user_id=int(user.id))
        await self.refresh_session_repository.create(
            session_id=session_id,
            user_id=int(user.id),
            tenant_id=tenant_id,
            token_version=resolved_token_version,
            device=device,
            expires_at=self._refresh_session_expiry(),
        )
        token_payload = {
            "sub": str(user.id),
            "tenant_id": tenant_id,
            "role": role.value,
            "tv": resolved_token_version,
        }
        return create_refresh_token_with_jti(token_payload, token_id=session_id)

    async def register(self, *, email: str, password: str, invite_token: str | None = None) -> User:
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
            tenant_id = settings.default_tenant_id
            role = UserRole.student

            if invite_token:
                invite_payload = decode_invite_token(invite_token)
                tenant_id = int(invite_payload["tenant_id"])
                role = UserRole(str(invite_payload["role"]))
                invite_email = invite_payload.get("email")
                if invite_email and str(invite_email).strip().lower() != email.strip().lower():
                    raise ValidationError("Invite token does not match this email address")

            tenant = await self.tenant_repository.get_by_id(tenant_id)
            if tenant is None:
                raise ValidationError("Invalid tenant")

            existing = await self.user_repository.get_by_email(email, tenant_id=tenant_id)
            if existing:
                raise ConflictError("Email already registered")

            user = await self.user_repository.create(
                tenant_id=tenant_id,
                email=email,
                password_hash=hash_password(password),
                role=role,
                created_at=datetime.now(timezone.utc),
            )
            await self.user_tenant_role_repository.ensure_membership(
                user_id=int(user.id),
                tenant_id=tenant_id,
                role=role,
            )
            await self.session.commit()
            await self.audit_log_service.record(
                tenant_id=tenant_id,
                user_id=int(user.id),
                action="auth.register",
                resource="user",
                metadata={"email": email, "role": role.value},
                commit=True,
            )
            self.logger.info(
                "auth register success",
                extra={
                    "log_data": {
                        "event": "auth.register.success",
                        "tenant_id": tenant_id,
                        "user_id": user.id,
                        "email": email,
                        "role": role.value,
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
        mfa_code: str | None = None,
    ) -> tuple[str, str, User, UserRole]:
        resolved_tenant_id = await self._resolve_login_tenant(
            tenant_id=tenant_id,
            tenant_subdomain=tenant_subdomain,
            request_host=request_host,
        )
        user = await self.user_repository.get_by_email(email, tenant_id=resolved_tenant_id)
        if user is None or not verify_password(password, user.password_hash):
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
            raise UnauthorizedError("Invalid email or password")
        if bool(getattr(user, "mfa_enabled", False)):
            secret = getattr(user, "mfa_secret", None)
            if not secret:
                raise UnauthorizedError("MFA is enabled but not configured correctly")
            if not mfa_code:
                raise UnauthorizedError("MFA code required")
            if not verify_totp_code(secret, mfa_code):
                raise UnauthorizedError("Invalid MFA code")
        membership = await self.user_tenant_role_repository.get_membership(
            user_id=int(user.id),
            tenant_id=resolved_tenant_id,
        )
        effective_role = membership.role if membership is not None else user.role
        token_version = await self._next_token_version(user_id=int(user.id))
        token_payload = {
            "sub": str(user.id),
            "tenant_id": resolved_tenant_id,
            "role": effective_role.value,
            "tv": token_version,
        }
        refresh_token = await self._create_refresh_session(
            user=user,
            tenant_id=resolved_tenant_id,
            role=effective_role,
            device=device,
            token_version=token_version,
        )
        access_token = create_access_token(token_payload, token_id=decode_refresh_token(refresh_token)["jti"])
        await self.session.commit()
        await self.audit_log_service.record(
            tenant_id=resolved_tenant_id,
            user_id=int(user.id),
            action="auth.login",
            resource="session",
            metadata={"email": email, "device": device},
            commit=True,
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
        return access_token, refresh_token, user, effective_role

    async def begin_mfa_setup(self, *, user_id: int, tenant_id: int) -> dict[str, str]:
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise ValidationError("User not found")
        secret = generate_totp_secret()
        user.mfa_secret = secret
        user.mfa_enabled = False
        await self.session.commit()
        issuer = "Learnova AI"
        return {
            "secret": secret,
            "manual_entry_code": secret,
            "otp_auth_url": build_totp_uri(secret=secret, account_name=user.email, issuer=issuer),
        }

    async def enable_mfa(self, *, user_id: int, tenant_id: int, code: str) -> User:
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise ValidationError("User not found")
        secret = getattr(user, "mfa_secret", None)
        if not secret:
            raise ValidationError("Start MFA setup before enabling it")
        if not verify_totp_code(secret, code):
            raise ValidationError("Invalid MFA code")
        user.mfa_enabled = True
        await self.session.commit()
        return user

    async def disable_mfa(self, *, user_id: int, tenant_id: int, code: str) -> User:
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise ValidationError("User not found")
        secret = getattr(user, "mfa_secret", None)
        if not user.mfa_enabled or not secret:
            raise ValidationError("MFA is not enabled")
        if not verify_totp_code(secret, code):
            raise ValidationError("Invalid MFA code")
        user.mfa_enabled = False
        user.mfa_secret = None
        await self.refresh_session_repository.revoke_for_user(user_id=user_id)
        await self.session.commit()
        return user

    async def refresh_session(self, refresh_token: str, *, device: str | None = None) -> tuple[str, str, User, UserRole]:
        payload = decode_refresh_token(refresh_token)
        try:
            user_id = int(payload["sub"])
            tenant_id = int(payload["tenant_id"])
            session_id = str(payload["jti"])
        except (KeyError, TypeError, ValueError) as exc:
            raise UnauthorizedError("Invalid refresh token") from exc

        refresh_session = await self.refresh_session_repository.get_active(session_id=session_id)
        if refresh_session is None or refresh_session.expires_at <= datetime.now(timezone.utc):
            raise UnauthorizedError("Refresh session expired or revoked")
        if int(payload.get("tv", refresh_session.token_version)) != int(refresh_session.token_version):
            raise UnauthorizedError("Refresh token version mismatch")

        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise UnauthorizedError("User not found")

        membership = await self.user_tenant_role_repository.get_membership(user_id=int(user.id), tenant_id=tenant_id)
        effective_role = membership.role if membership is not None else user.role
        await self.refresh_session_repository.revoke(refresh_session)
        token_payload = {
            "sub": str(user.id),
            "tenant_id": tenant_id,
            "role": effective_role.value,
            "tv": int(refresh_session.token_version),
        }
        next_refresh_token = await self._create_refresh_session(
            user=user,
            tenant_id=tenant_id,
            role=effective_role,
            device=device or refresh_session.device,
            token_version=int(refresh_session.token_version),
        )
        await self.session.commit()
        return create_access_token(token_payload, token_id=decode_refresh_token(next_refresh_token)["jti"]), next_refresh_token, user, effective_role

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        try:
            payload = decode_refresh_token(refresh_token)
            session_id = str(payload["jti"])
        except Exception:
            return
        revoked = await self.refresh_session_repository.revoke_by_id(session_id=session_id)
        if revoked:
            await self.session.commit()
            try:
                user_id = int(payload["sub"])
                tenant_id = int(payload["tenant_id"])
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

    async def request_email_verification(self, *, tenant_id: int, email: str) -> str:
        user = await self.user_repository.get_by_email(email, tenant_id=tenant_id)
        if user is None:
            raise ValidationError("User not found")
        token = create_email_verification_token(user_id=int(user.id), tenant_id=tenant_id, email=user.email)
        await self._queue_email_verification_email(email=user.email, token=token)
        return token

    async def verify_email(self, *, token: str) -> User:
        payload = decode_email_verification_token(token)
        user_id = int(payload["sub"])
        tenant_id = int(payload["tenant_id"])
        email = str(payload["email"])
        user = await self.user_repository.get_by_email(email, tenant_id=tenant_id)
        if user is None or int(user.id) != user_id:
            raise ValidationError("Invalid verification token")
        user.email_verified_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.audit_log_service.record(
            tenant_id=tenant_id,
            user_id=user_id,
            action="auth.verify_email",
            resource="user",
            metadata={"email": email},
            commit=True,
        )
        return user

    async def request_password_reset(self, *, tenant_id: int, email: str) -> str:
        user = await self.user_repository.get_by_email(email, tenant_id=tenant_id)
        if user is None:
            raise ValidationError("User not found")
        token = create_password_reset_token(user_id=int(user.id), tenant_id=tenant_id, email=user.email)
        await self._queue_password_reset_email(email=user.email, token=token)
        return token

    async def reset_password(self, *, token: str, password: str) -> User:
        try:
            validate_password_strength(password)
        except PasswordValidationError as exc:
            raise ValidationError(str(exc)) from exc
        payload = decode_password_reset_token(token)
        user_id = int(payload["sub"])
        tenant_id = int(payload["tenant_id"])
        email = str(payload["email"])
        user = await self.user_repository.get_by_email(email, tenant_id=tenant_id)
        if user is None or int(user.id) != user_id:
            raise ValidationError("Invalid reset token")
        user.password_hash = hash_password(password)
        await self.refresh_session_repository.revoke_for_user(user_id=user_id)
        await self.session.commit()
        await self.audit_log_service.record(
            tenant_id=tenant_id,
            user_id=user_id,
            action="auth.reset_password",
            resource="user",
            metadata={"email": email},
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

    async def _queue_email_verification_email(self, *, email: str, token: str) -> None:
        verification_url = f"{self._frontend_origin()}/auth?mode=email-verification&token={token}"
        payload = self.email_service.build_verification_email(to_email=email, verification_url=verification_url)
        await self._enqueue_email(payload)

    async def _queue_password_reset_email(self, *, email: str, token: str) -> None:
        reset_url = f"{self._frontend_origin()}/auth?mode=reset-password&token={token}"
        payload = self.email_service.build_password_reset_email(to_email=email, reset_url=reset_url)
        await self._enqueue_email(payload)

    async def _queue_invite_email(self, *, email: str, role: UserRole, invite_token: str) -> None:
        invite_url = f"{self._frontend_origin()}/auth?mode=invite&invite={invite_token}"
        payload = self.email_service.build_invite_email(to_email=email, invite_url=invite_url, role_label=role.value)
        await self._enqueue_email(payload)

    async def _enqueue_email(self, payload) -> None:
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
