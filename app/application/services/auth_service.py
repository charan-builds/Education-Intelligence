from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import (
    PasswordValidationError,
    create_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.domain.models.user import User
from app.domain.models.user import UserRole
from app.infrastructure.repositories.tenant_repository import TenantRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.application.exceptions import ConflictError, UnauthorizedError, ValidationError


class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repository = UserRepository(session)
        self.tenant_repository = TenantRepository(session)
        self.session = session
        self.logger = get_logger()

    async def register(self, tenant_id: int, email: str, password: str, role: UserRole) -> User:
        try:
            try:
                validate_password_strength(password)
            except PasswordValidationError as exc:
                self.logger.warning(
                    "auth register rejected",
                    extra={"log_data": {"event": "auth.register.rejected", "email": email}},
                )
                raise ValidationError(str(exc)) from exc

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
            self.logger.info(
                "auth register success",
                extra={
                    "log_data": {
                        "event": "auth.register.success",
                        "tenant_id": tenant_id,
                        "user_id": user.id,
                        "email": email,
                    }
                },
            )
            return user
        except Exception:
            await self.session.rollback()
            raise

    async def login(self, email: str, password: str) -> tuple[str, User]:
        user = await self.user_repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            self.logger.warning(
                "auth login failed",
                extra={"log_data": {"event": "auth.login.failed", "email": email}},
            )
            raise UnauthorizedError("Invalid email or password")
        token = create_access_token({"sub": str(user.id), "tenant_id": user.tenant_id, "role": user.role.value})
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
        return token, user
