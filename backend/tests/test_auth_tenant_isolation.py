import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.application.exceptions import UnauthorizedError, ValidationError
import app.application.services.auth_service as auth_service_module
from app.application.services.auth_service import AuthService
from app.core.security import hash_password
from app.domain.models.tenant import TenantType
from app.domain.models.user import UserRole


@dataclass
class _Tenant:
    id: int
    name: str
    type: TenantType
    subdomain: str | None = None


@dataclass
class _User:
    id: int
    tenant_id: int
    email: str
    password_hash: str
    role: UserRole
    email_verified_at: datetime | None = None


class _Session:
    async def commit(self):
        return None

    async def rollback(self):
        return None


class _AuthLogRepository:
    async def create(self, **kwargs):
        return type("_AuthLog", (), kwargs)()


class _AuthTokenRepository:
    def __init__(self):
        self.tokens: dict[tuple[str, str], object] = {}

    async def invalidate_active_tokens_for_user(self, *, user_id: int, purpose):
        _ = user_id, purpose
        return 0

    async def create(self, *, user_id: int, tenant_id: int, purpose, token_hash: str, expires_at: datetime, created_at: datetime):
        row = type(
            "_AuthToken",
            (),
            {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "purpose": purpose,
                "token_hash": token_hash,
                "expires_at": expires_at,
                "created_at": created_at,
                "used_at": None,
            },
        )()
        self.tokens[(purpose.value if hasattr(purpose, "value") else str(purpose), token_hash)] = row
        return row

    async def get_active_by_hash(self, *, token_hash: str, purpose):
        row = self.tokens.get((purpose.value if hasattr(purpose, "value") else str(purpose), token_hash))
        if row is None or row.used_at is not None:
            return None
        return row

    async def mark_used(self, row):
        row.used_at = datetime.now(timezone.utc)


class _RefreshRepo:
    def __init__(self):
        self.revoked_user_id: int | None = None

    async def create(self, **kwargs):
        return type("_RefreshSession", (), kwargs)()

    async def revoke_for_user(self, *, user_id: int):
        self.revoked_user_id = user_id
        return 1

    async def list_active_for_user(self, *, user_id: int):
        return []


class _AuditLogService:
    async def record(self, **kwargs):
        return None


class _EmailService:
    def build_verification_email(
        self,
        *,
        to_email: str,
        verification_url: str,
        tenant_id: int,
        account_email: str,
        sign_in_url: str,
    ):
        _ = tenant_id, account_email, sign_in_url
        return type("Payload", (), {"to_email": to_email, "subject": "verify", "html_content": verification_url, "text_content": verification_url})()

    def build_password_reset_email(self, *, to_email: str, reset_url: str):
        return type("Payload", (), {"to_email": to_email, "subject": "reset", "html_content": reset_url, "text_content": reset_url})()

    async def send(self, payload):
        return payload


class _SessionService:
    async def next_token_version(self, *, user_id: int):
        _ = user_id
        return 1

    async def create_session_tokens(
        self,
        *,
        user,
        tenant_id: int,
        role,
        device: str | None,
        ip_address: str | None,
        token_version: int,
        scope: str,
        include_refresh_token: bool = True,
    ):
        _ = user, tenant_id, role, device, ip_address, token_version
        return "access-token", ("refresh-token" if include_refresh_token else None), f"session-{scope}"

    @staticmethod
    def lockout_deadline(*, failed_attempts: int, threshold: int = 5):
        _ = failed_attempts, threshold
        return None


class _MembershipRepo:
    def __init__(self):
        self.roles = {
            (1, 1): UserRole.student,
            (2, 2): UserRole.student,
        }

    async def get_membership(self, *, user_id: int, tenant_id: int):
        role = self.roles.get((user_id, tenant_id))
        if role is None:
            return None
        return type("_Membership", (), {"user_id": user_id, "tenant_id": tenant_id, "role": role})()

    async def ensure_membership(self, *, user_id: int, tenant_id: int, role: UserRole):
        self.roles[(user_id, tenant_id)] = role
        return type("_Membership", (), {"user_id": user_id, "tenant_id": tenant_id, "role": role})()


class _TenantRepo:
    def __init__(self):
        self.by_id = {
            1: _Tenant(id=1, name="Northwind", type=TenantType.school, subdomain="northwind"),
            2: _Tenant(id=2, name="Acme", type=TenantType.company, subdomain="acme"),
            3: _Tenant(id=3, name="Solo Workspace", type=TenantType.personal, subdomain="solo-workspace"),
        }

    async def get_by_id(self, tenant_id: int):
        return self.by_id.get(tenant_id)

    async def get_by_subdomain(self, subdomain: str):
        return next((tenant for tenant in self.by_id.values() if tenant.subdomain == subdomain), None)


class _UserRepo:
    def __init__(self):
        self.users = {
            (1, "student@example.com"): _User(
                id=1,
                tenant_id=1,
                email="student@example.com",
                password_hash=hash_password("northwind123"),
                role=UserRole.student,
                email_verified_at=datetime.now(timezone.utc),
            ),
            (2, "student@example.com"): _User(
                id=2,
                tenant_id=2,
                email="student@example.com",
                password_hash=hash_password("acme12345"),
                role=UserRole.student,
                email_verified_at=datetime.now(timezone.utc),
            ),
            (3, "solo@example.com"): _User(
                id=3,
                tenant_id=3,
                email="solo@example.com",
                password_hash=hash_password("solo12345"),
                role=UserRole.independent_learner,
                email_verified_at=datetime.now(timezone.utc),
            ),
        }

    async def get_by_email(self, email: str, *, tenant_id: int | None = None):
        return self.users.get((tenant_id, email))

    async def list_by_email(self, email: str):
        return [user for (_tenant_id, user_email), user in self.users.items() if user_email == email]

    async def get_by_id_in_tenant(self, user_id: int, tenant_id: int):
        user = next((item for item in self.users.values() if item.id == user_id and item.tenant_id == tenant_id), None)
        return user


def _build_service() -> AuthService:
    auth_service_module.hash_password = hash_password
    auth_service_module.verify_password = auth_service_module.verify_password.__globals__["pwd_context"].verify if False else auth_service_module.verify_password
    service = AuthService(_Session())
    service.tenant_repository = _TenantRepo()
    service.user_repository = _UserRepo()
    service.refresh_session_repository = _RefreshRepo()
    service.audit_log_service = _AuditLogService()
    service.user_tenant_role_repository = _MembershipRepo()
    service.session_service = _SessionService()
    service.email_service = _EmailService()
    service.auth_log_repository = _AuthLogRepository()
    service.auth_token_repository = _AuthTokenRepository()

    async def _fake_enqueue_email(payload, background_tasks=None):
        _ = background_tasks
        return await service.email_service.send(payload)

    service._enqueue_email = _fake_enqueue_email  # type: ignore[method-assign]
    return service


def test_login_requires_tenant_context():
    async def _run():
        service = _build_service()
        service.user_tenant_role_repository = _MembershipRepo()

        with pytest.raises(ValidationError):
            await service.login(email="student@example.com", password="northwind123")

    asyncio.run(_run())


def test_login_isolated_by_tenant_id():
    async def _run():
        service = _build_service()

        result = await service.login(
            email="student@example.com",
            password="northwind123",
            tenant_id=1,
        )
        assert result.user.id == 1
        assert result.effective_role == UserRole.student

        with pytest.raises(UnauthorizedError):
            await service.login(
                email="student@example.com",
                password="northwind123",
                tenant_id=2,
            )

    asyncio.run(_run())


def test_login_supports_subdomain_resolution():
    async def _run():
        service = _build_service()

        result = await service.login(
            email="student@example.com",
            password="acme12345",
            tenant_subdomain="acme",
        )
        assert result.user.tenant_id == 2
        assert result.effective_role == UserRole.student

    asyncio.run(_run())


def test_email_verification_and_password_reset():
    async def _run():
        service = _build_service()
        refresh_repo = _RefreshRepo()
        service.refresh_session_repository = refresh_repo

        verification_token = await service.request_email_verification(tenant_id=1, email="student@example.com")
        verified_user = await service.verify_email(token=verification_token)
        assert verified_user.email_verified_at is not None

        reset_token = await service.request_password_reset(tenant_id=1, email="student@example.com")
        reset_user = await service.reset_password(token=reset_token, password="Updated1234!")
        assert refresh_repo.revoked_user_id == reset_user.id

        result = await service.login(
            email="student@example.com",
            password="Updated1234!",
            tenant_id=1,
        )
        assert result.user.id == reset_user.id

    asyncio.run(_run())


def test_independent_learner_login_can_infer_personal_tenant():
    async def _run():
        service = _build_service()
        service.user_tenant_role_repository.roles[(3, 3)] = UserRole.independent_learner

        with pytest.raises(UnauthorizedError):
            await service.login(
                email="solo@example.com",
                password="bad-password",
            )

    asyncio.run(_run())
