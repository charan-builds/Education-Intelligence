import asyncio
from dataclasses import dataclass

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
    email_verified_at: object | None = None


class _Session:
    async def commit(self):
        return None

    async def rollback(self):
        return None


class _RefreshRepo:
    async def create(self, **kwargs):
        return type("_RefreshSession", (), kwargs)()

    async def revoke_for_user(self, *, user_id: int):
        return 1


class _AuthTokenRepo:
    async def invalidate_active_tokens_for_user(self, *, user_id: int, purpose):
        return 0

    async def create(self, **kwargs):
        return type("_AuthToken", (), kwargs)()


class _AuthLogRepo:
    async def create(self, **kwargs):
        return type("_AuthLog", (), kwargs)()


class _MembershipRepo:
    async def get_membership(self, *, user_id: int, tenant_id: int):
        return type("_Membership", (), {"user_id": user_id, "tenant_id": tenant_id, "role": UserRole.student})()


class _TenantRepo:
    async def get_by_id(self, tenant_id: int):
        return _Tenant(id=tenant_id, name="Northwind", type=TenantType.school, subdomain="northwind")

    async def get_by_subdomain(self, subdomain: str):
        return _Tenant(id=1, name="Northwind", type=TenantType.school, subdomain=subdomain)


class _UserRepo:
    def __init__(self):
        self.users = {
            (1, "student@example.com"): _User(
                id=1,
                tenant_id=1,
                email="student@example.com",
                password_hash=hash_password("northwind123"),
                role=UserRole.student,
            )
        }

    async def get_by_email(self, email: str, *, tenant_id: int | None = None):
        return self.users.get((tenant_id, email))

    async def get_by_id_in_tenant(self, user_id: int, tenant_id: int):
        return next((item for item in self.users.values() if item.id == user_id and item.tenant_id == tenant_id), None)


class _AuditLogService:
    async def record(self, **kwargs):
        return None


def test_auth_requests_queue_email_jobs(monkeypatch):
    queued: list[dict[str, str]] = []

    class _EmailTask:
        @staticmethod
        def delay(**kwargs):
            queued.append(kwargs)

    monkeypatch.setattr("app.infrastructure.jobs.tasks.send_email", _EmailTask)

    async def _run():
        service = AuthService(_Session())
        service.tenant_repository = _TenantRepo()
        service.user_repository = _UserRepo()
        service.refresh_session_repository = _RefreshRepo()
        service.auth_token_repository = _AuthTokenRepo()
        service.auth_log_repository = _AuthLogRepo()
        service.audit_log_service = _AuditLogService()
        service.user_tenant_role_repository = _MembershipRepo()

        verification_token = await service.request_email_verification(tenant_id=1, email="student@example.com")
        reset_token = await service.request_password_reset(tenant_id=1, email="student@example.com")
        invite_token = await service.create_invite(
            actor_role=UserRole.admin,
            tenant_id=1,
            role=UserRole.mentor,
            email="mentor@example.com",
        )

        assert verification_token
        assert reset_token
        assert invite_token

    asyncio.run(_run())

    assert len(queued) == 3
    assert queued[0]["to_email"] == "student@example.com"
    assert "Verify your Learning Intelligence account" == queued[0]["subject"]
    assert queued[1]["to_email"] == "student@example.com"
    assert "Reset your Learning Intelligence password" == queued[1]["subject"]
    assert queued[2]["to_email"] == "mentor@example.com"
    assert "Your Learning Intelligence invitation" == queued[2]["subject"]
