from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.application.exceptions import UnauthorizedError
from app.core.security import hash_token_value
from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.repositories.token_blacklist_repository import TokenBlacklistRepository
from app.application.services.token_service import TokenService


class SessionService:
    def __init__(
        self,
        *,
        session_repository: SessionRepository,
        refresh_token_repository: RefreshTokenRepository,
        token_blacklist_repository: TokenBlacklistRepository,
        token_service: TokenService,
    ) -> None:
        self.session_repository = session_repository
        self.refresh_token_repository = refresh_token_repository
        self.token_blacklist_repository = token_blacklist_repository
        self.token_service = token_service

    async def next_token_version(self, *, user_id: int) -> int:
        return await self.session_repository.next_token_version_for_user(user_id=user_id)

    async def create_session_tokens(
        self,
        *,
        user: User,
        tenant_id: int,
        role: UserRole,
        device: str | None,
        ip_address: str | None,
        token_version: int,
        scope: str,
        include_refresh_token: bool = True,
    ) -> tuple[str, str | None, str]:
        session_id = uuid4().hex
        await self.session_repository.create(
            session_id=session_id,
            user_id=int(user.id),
            tenant_id=tenant_id,
            token_version=token_version,
            device=device,
            expires_at=self.token_service.refresh_session_expiry(),
        )
        refresh_token: str | None = None
        if include_refresh_token:
            refresh_token = await self.token_service.issue_refresh_token(
                user=user,
                tenant_id=tenant_id,
                role=role,
                session_id=session_id,
                token_version=token_version,
                device=device,
                ip_address=ip_address,
            )
        access_token = self.token_service.build_access_token(
            user=user,
            tenant_id=tenant_id,
            role=role,
            token_version=token_version,
            session_id=session_id,
            scope=scope,
        )
        return access_token, refresh_token, session_id

    async def rotate_refresh_session(
        self,
        *,
        refresh_token: str,
        user: User,
        tenant_id: int,
        role: UserRole,
        device: str | None,
        ip_address: str | None,
    ) -> tuple[str, str]:
        payload = self.token_service.decode_refresh(refresh_token)
        try:
            session_id = str(payload["jti"])
        except (KeyError, TypeError, ValueError) as exc:
            raise UnauthorizedError("Invalid refresh token") from exc

        refresh_session = await self.session_repository.get_active(session_id=session_id)
        if refresh_session is None or refresh_session.expires_at <= datetime.now(timezone.utc):
            raise UnauthorizedError("Refresh session expired or revoked")

        persisted_refresh_token = await self.refresh_token_repository.get_active_by_hash(
            token_hash=hash_token_value(refresh_token)
        )
        if persisted_refresh_token is None or persisted_refresh_token.token_jti != session_id:
            raise UnauthorizedError("Refresh token expired or revoked")
        if int(payload.get("tv", refresh_session.token_version)) != int(refresh_session.token_version):
            raise UnauthorizedError("Refresh token version mismatch")

        await self.session_repository.revoke(refresh_session)
        access_token, next_refresh_token, _ = await self.create_session_tokens(
            user=user,
            tenant_id=tenant_id,
            role=role,
            device=device or refresh_session.device,
            ip_address=ip_address,
            token_version=int(refresh_session.token_version),
            scope="full_access",
            include_refresh_token=True,
        )
        await self.refresh_token_repository.revoke(persisted_refresh_token)
        return access_token, next_refresh_token or ""

    async def revoke_refresh_session(self, *, refresh_token: str | None) -> tuple[bool, dict | None]:
        if not refresh_token:
            return False, None
        try:
            payload = self.token_service.decode_refresh(refresh_token)
            session_id = str(payload["jti"])
        except Exception:
            return False, None

        revoked = await self.session_repository.revoke_by_id(session_id=session_id)
        persisted_refresh_token = await self.refresh_token_repository.get_active_by_hash(
            token_hash=hash_token_value(refresh_token)
        )
        if persisted_refresh_token is not None:
            await self.refresh_token_repository.revoke(persisted_refresh_token)
        return revoked, payload

    async def blacklist_access_token(self, access_token: str) -> None:
        payload = self.token_service.decode_access(access_token)
        expires_at = datetime.fromtimestamp(float(payload["exp"]), tz=timezone.utc) if payload.get("exp") is not None else None
        await self.token_blacklist_repository.add(
            token_jti=str(payload["jti"]),
            user_id=int(payload["sub"]),
            tenant_id=int(payload["tenant_id"]) if payload.get("tenant_id") is not None else None,
            token_type="access",
            expires_at=expires_at,
        )

    @staticmethod
    def lockout_deadline(*, failed_attempts: int, threshold: int = 5) -> datetime | None:
        if failed_attempts < threshold:
            return None
        return datetime.now(timezone.utc) + timedelta(minutes=15)
