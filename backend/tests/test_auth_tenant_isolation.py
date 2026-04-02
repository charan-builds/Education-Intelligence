import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.application.exceptions import UnauthorizedError, ValidationError
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
            ),
            (2, "student@example.com"): _User(
                id=2,
                tenant_id=2,
                email="student@example.com",
                password_hash=hash_password("acme12345"),
                role=UserRole.student,
            ),
        }

    async def get_by_email(self, email: str, *, tenant_id: int | None = None):
        return self.users.get((tenant_id, email))

    async def get_by_id_in_tenant(self, user_id: int, tenant_id: int):
        user = next((item for item in self.users.values() if item.id == user_id and item.tenant_id == tenant_id), None)
        return user


def test_login_requires_tenant_context():
    async def _run():
        service = AuthService(_Session())
        service.tenant_repository = _TenantRepo()
        service.user_repository = _UserRepo()
        service.refresh_session_repository = _RefreshRepo()
        service.audit_log_service = _AuditLogService()
        service.user_tenant_role_repository = _MembershipRepo()
        service.user_tenant_role_repository = _MembershipRepo()

        with pytest.raises(ValidationError):
            await service.login(email="student@example.com", password="northwind123")

    asyncio.run(_run())


def test_login_isolated_by_tenant_id():
    async def _run():
        service = AuthService(_Session())
        service.tenant_repository = _TenantRepo()
        service.user_repository = _UserRepo()
        service.refresh_session_repository = _RefreshRepo()
        service.audit_log_service = _AuditLogService()
        service.user_tenant_role_repository = _MembershipRepo()

        _, _, user, role = await service.login(
            email="student@example.com",
            password="northwind123",
            tenant_id=1,
        )
        assert user.id == 1
        assert role == UserRole.student

        with pytest.raises(UnauthorizedError):
            await service.login(
                email="student@example.com",
                password="northwind123",
                tenant_id=2,
            )

    asyncio.run(_run())


def test_login_supports_subdomain_resolution():
    async def _run():
        service = AuthService(_Session())
        service.tenant_repository = _TenantRepo()
        service.user_repository = _UserRepo()
        service.refresh_session_repository = _RefreshRepo()
        service.audit_log_service = _AuditLogService()
        service.user_tenant_role_repository = _MembershipRepo()

        _, _, user, role = await service.login(
            email="student@example.com",
            password="acme12345",
            tenant_subdomain="acme",
        )
        assert user.tenant_id == 2
        assert role == UserRole.student

    asyncio.run(_run())


def test_email_verification_and_password_reset():
    async def _run():
        service = AuthService(_Session())
        service.tenant_repository = _TenantRepo()
        service.user_repository = _UserRepo()
        refresh_repo = _RefreshRepo()
        service.refresh_session_repository = refresh_repo
        service.audit_log_service = _AuditLogService()
        service.user_tenant_role_repository = _MembershipRepo()

        verification_token = await service.request_email_verification(tenant_id=1, email="student@example.com")
        verified_user = await service.verify_email(token=verification_token)
        assert verified_user.email_verified_at is not None

        reset_token = await service.request_password_reset(tenant_id=1, email="student@example.com")
        reset_user = await service.reset_password(token=reset_token, password="updated1234")
        assert refresh_repo.revoked_user_id == reset_user.id

        _, _, logged_in_user, _ = await service.login(
            email="student@example.com",
            password="updated1234",
            tenant_id=1,
        )
        assert logged_in_user.id == reset_user.id

    asyncio.run(_run())
