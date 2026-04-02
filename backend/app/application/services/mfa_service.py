from __future__ import annotations

from app.application.exceptions import ValidationError
from app.core.security import build_totp_uri, generate_totp_secret, verify_totp_code
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.repositories.user_repository import UserRepository


class MFAService:
    def __init__(self, *, user_repository: UserRepository, session_repository: SessionRepository) -> None:
        self.user_repository = user_repository
        self.session_repository = session_repository

    async def begin_setup(self, *, user_id: int, tenant_id: int) -> dict[str, str]:
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise ValidationError("User not found")
        secret = generate_totp_secret()
        user.mfa_secret = secret
        user.mfa_enabled = False
        return {
            "secret": secret,
            "manual_entry_code": secret,
            "otp_auth_url": build_totp_uri(secret=secret, account_name=user.email, issuer="Learnova AI"),
        }

    async def enable(self, *, user_id: int, tenant_id: int, code: str):
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise ValidationError("User not found")
        secret = getattr(user, "mfa_secret", None)
        if not secret:
            raise ValidationError("Start MFA setup before enabling it")
        if not verify_totp_code(secret, code):
            raise ValidationError("Invalid MFA code")
        user.mfa_enabled = True
        return user

    async def disable(self, *, user_id: int, tenant_id: int, code: str):
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
        await self.session_repository.revoke_for_user(user_id=user_id)
        return user
