from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.application.services.audit_log_service import AuditLogService
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import (
    PasswordValidationError,
    create_access_token,
    create_invite_token,
    create_refresh_token_with_jti,
    decode_invite_token,
    decode_refresh_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.refresh_session_repository import RefreshSessionRepository
from app.infrastructure.repositories.tenant_repository import TenantRepository
from app.infrastructure.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repository = UserRepository(session)
        self.refresh_session_repository = RefreshSessionRepository(session)
        self.tenant_repository = TenantRepository(session)
        self.session = session
        self.logger = get_logger()
        self.audit_log_service = AuditLogService(session)

    @staticmethod
    def _refresh_session_expiry() -> datetime:
        settings = get_settings()
        return datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes)

    async def _create_refresh_session(self, *, user: User, device: str | None) -> str:
        session_id = uuid4().hex
        await self.refresh_session_repository.create(
            session_id=session_id,
            user_id=int(user.id),
            device=device,
            expires_at=self._refresh_session_expiry(),
        )
        token_payload = {"sub": str(user.id), "tenant_id": user.tenant_id, "role": user.role.value}
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

            existing = await self.user_repository.get_by_email(email)
            if existing:
                raise ConflictError("Email already registered")

            user = await self.user_repository.create(
                tenant_id=tenant_id,
                email=email,
                password_hash=hash_password(password),
                role=role,
                created_at=datetime.now(timezone.utc),
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

    async def login(self, email: str, password: str, *, device: str | None = None) -> tuple[str, str, User]:
        user = await self.user_repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            self.logger.warning(
                "auth login failed",
                extra={"log_data": {"event": "auth.login.failed", "email": email}},
            )
            raise UnauthorizedError("Invalid email or password")
        token_payload = {"sub": str(user.id), "tenant_id": user.tenant_id, "role": user.role.value}
        access_token = create_access_token(token_payload)
        refresh_token = await self._create_refresh_session(user=user, device=device)
        await self.session.commit()
        await self.audit_log_service.record(
            tenant_id=int(user.tenant_id),
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
                    "tenant_id": user.tenant_id,
                    "user_id": user.id,
                    "email": email,
                }
            },
        )
        return access_token, refresh_token, user

    async def refresh_session(self, refresh_token: str, *, device: str | None = None) -> tuple[str, str, User]:
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

        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise UnauthorizedError("User not found")

        token_payload = {"sub": str(user.id), "tenant_id": user.tenant_id, "role": user.role.value}
        await self.refresh_session_repository.revoke(refresh_session)
        next_refresh_token = await self._create_refresh_session(user=user, device=device or refresh_session.device)
        await self.session.commit()
        return create_access_token(token_payload), next_refresh_token, user

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
        return create_invite_token(tenant_id=tenant_id, role=role.value, email=email)
