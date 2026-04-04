from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

import app.application.services.auth_service as auth_service_module
from app.application.exceptions import UnauthorizedError, ValidationError
from app.application.services.auth_service import AuthService
from app.application.services.session_service import SessionService
from app.application.services.token_service import TokenService
from app.application.services.user_service import UserService
from app.domain.models.auth_token import AuthTokenPurpose
from app.domain.models.tenant import TenantType
from app.domain.models.user import UserRole


@dataclass
class _Tenant:
    id: int
    name: str
    subdomain: str
    type: TenantType


@dataclass
class _Membership:
    user_id: int
    tenant_id: int
    role: UserRole
    created_at: datetime
    updated_at: datetime


@dataclass
class _User:
    id: int
    tenant_id: int
    email: str
    password_hash: str
    role: UserRole
    created_at: datetime
    full_name: str | None = None
    display_name: str | None = None
    phone_number: str | None = None
    linkedin_url: str | None = None
    college_name: str | None = None
    avatar_url: str | None = None
    preferences_json: dict | None = None
    is_email_verified: bool = False
    is_phone_verified: bool = False
    email_verified_at: datetime | None = None
    is_profile_completed: bool = False
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    mfa_enabled: bool = False
    mfa_secret: str | None = None


@dataclass
class _AuthToken:
    id: int
    user_id: int
    tenant_id: int
    purpose: AuthTokenPurpose
    token_hash: str
    expires_at: datetime
    created_at: datetime
    used_at: datetime | None = None


@dataclass
class _AuthLog:
    tenant_id: int | None
    user_id: int | None
    email: str | None
    event_type: str
    status: str
    ip_address: str | None
    user_agent: str | None
    detail: str | None
    metadata: dict | None


@dataclass
class _SessionRecord:
    id: str
    user_id: int
    tenant_id: int
    token_version: int
    device: str | None
    expires_at: datetime
    revoked: bool = False
    created_at: datetime = datetime.now(timezone.utc)
    revoked_at: datetime | None = None


@dataclass
class _RefreshToken:
    id: int
    user_id: int
    tenant_id: int
    token_hash: str
    token_jti: str
    device_info: str | None
    ip_address: str | None
    expires_at: datetime
    metadata_json: dict
    is_revoked: bool = False
    created_at: datetime = datetime.now(timezone.utc)
    revoked_at: datetime | None = None


@dataclass
class _TokenBlacklist:
    token_jti: str
    user_id: int | None
    tenant_id: int | None
    token_type: str
    expires_at: datetime | None


class _DummyAuditLogService:
    async def record(self, **kwargs):  # noqa: ANN003
        return kwargs


class _DummyEmailService:
    def build_verification_email(
        self,
        *,
        to_email: str,
        verification_url: str,
        tenant_id: int,
        account_email: str,
        sign_in_url: str,
    ):
        return type("Payload", (), {"to_email": to_email, "subject": "verify", "html_content": verification_url, "text_content": verification_url})()

    def build_password_reset_email(self, *, to_email: str, reset_url: str):
        return type("Payload", (), {"to_email": to_email, "subject": "reset", "html_content": reset_url, "text_content": reset_url})()

    async def send(self, payload):  # noqa: ANN001
        return {"delivered": True, "to_email": payload.to_email}


def _fast_hash_password(password: str) -> str:
    return f"test-hash::{password}"


def _fast_verify_password(password: str, password_hash: str) -> bool:
    return password_hash == _fast_hash_password(password)


class _FakeSession:
    async def commit(self):
        return None

    async def rollback(self):
        return None

    async def flush(self):
        return None

    async def refresh(self, _obj):
        return None

    def add(self, _obj):
        return None


class _Store:
    def __init__(self) -> None:
        self.tenants = {
            1: _Tenant(id=1, name="Platform", subdomain="platform", type=TenantType.platform),
            2: _Tenant(id=2, name="Demo University", subdomain="demo", type=TenantType.college),
        }
        self.users_by_id: dict[int, _User] = {}
        self.users_by_email: dict[tuple[int, str], _User] = {}
        self.memberships: dict[tuple[int, int], _Membership] = {}
        self.auth_tokens: list[_AuthToken] = []
        self.auth_logs: list[_AuthLog] = []
        self.sessions: dict[str, _SessionRecord] = {}
        self.refresh_tokens: list[_RefreshToken] = []
        self.token_blacklist: list[_TokenBlacklist] = []
        self.next_tenant_id = 3
        self.next_user_id = 1
        self.next_auth_token_id = 1
        self.next_refresh_token_id = 1


class _TenantRepository:
    def __init__(self, store: _Store) -> None:
        self.store = store

    async def get_by_id(self, tenant_id: int):
        return self.store.tenants.get(tenant_id)

    async def get_by_subdomain(self, subdomain: str):
        for tenant in self.store.tenants.values():
            if tenant.subdomain == subdomain:
                return tenant
        return None

    async def create(self, name: str, tenant_type: TenantType, created_at, *, subdomain: str | None = None):
        tenant = _Tenant(
            id=self.store.next_tenant_id,
            name=name,
            subdomain=subdomain,
            type=tenant_type,
        )
        self.store.next_tenant_id += 1
        self.store.tenants[tenant.id] = tenant
        return tenant


class _UserRepository:
    def __init__(self, store: _Store) -> None:
        self.store = store

    async def create(
        self,
        tenant_id: int,
        email: str,
        password_hash: str,
        role: UserRole,
        created_at,
        *,
        full_name: str | None = None,
        display_name: str | None = None,
        phone_number: str | None = None,
        linkedin_url: str | None = None,
        college_name: str | None = None,
        is_email_verified: bool = False,
        is_profile_completed: bool = False,
    ):
        user = _User(
            id=self.store.next_user_id,
            tenant_id=tenant_id,
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
            created_at=created_at,
            full_name=full_name,
            display_name=display_name,
            phone_number=phone_number,
            linkedin_url=linkedin_url,
            college_name=college_name,
            is_email_verified=is_email_verified,
            is_profile_completed=is_profile_completed,
        )
        self.store.next_user_id += 1
        self.store.users_by_id[user.id] = user
        self.store.users_by_email[(tenant_id, user.email)] = user
        return user

    async def get_by_email(self, email: str, *, tenant_id: int | None = None):
        normalized = email.strip().lower()
        if tenant_id is not None:
            return self.store.users_by_email.get((tenant_id, normalized))
        for (stored_tenant_id, stored_email), user in self.store.users_by_email.items():
            if stored_email == normalized:
                return user
        return None

    async def list_by_email(self, email: str):
        normalized = email.strip().lower()
        return [user for (_tenant_id, stored_email), user in self.store.users_by_email.items() if stored_email == normalized]

    async def get_by_id_in_tenant(self, user_id: int, tenant_id: int):
        user = self.store.users_by_id.get(user_id)
        if user is None or user.tenant_id != tenant_id:
            return None
        return user


class _UserTenantRoleRepository:
    def __init__(self, store: _Store) -> None:
        self.store = store

    async def ensure_membership(self, *, user_id: int, tenant_id: int, role: UserRole):
        now = datetime.now(timezone.utc)
        membership = self.store.memberships.get((user_id, tenant_id))
        if membership is None:
            membership = _Membership(user_id=user_id, tenant_id=tenant_id, role=role, created_at=now, updated_at=now)
            self.store.memberships[(user_id, tenant_id)] = membership
        else:
            membership.role = role
            membership.updated_at = now
        return membership

    async def get_membership(self, *, user_id: int, tenant_id: int):
        return self.store.memberships.get((user_id, tenant_id))


class _AuthTokenRepository:
    def __init__(self, store: _Store) -> None:
        self.store = store

    async def create(self, *, user_id: int, tenant_id: int, purpose: AuthTokenPurpose, token_hash: str, expires_at: datetime, created_at: datetime):
        row = _AuthToken(
            id=self.store.next_auth_token_id,
            user_id=user_id,
            tenant_id=tenant_id,
            purpose=purpose,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=created_at,
        )
        self.store.next_auth_token_id += 1
        self.store.auth_tokens.append(row)
        return row

    async def invalidate_active_tokens_for_user(self, *, user_id: int, purpose: AuthTokenPurpose) -> int:
        count = 0
        for row in self.store.auth_tokens:
            if row.user_id == user_id and row.purpose == purpose and row.used_at is None:
                row.used_at = datetime.now(timezone.utc)
                count += 1
        return count

    async def get_active_by_hash(self, *, token_hash: str, purpose: AuthTokenPurpose):
        now = datetime.now(timezone.utc)
        for row in self.store.auth_tokens:
            if row.token_hash == token_hash and row.purpose == purpose and row.used_at is None and row.expires_at > now:
                return row
        return None

    async def mark_used(self, row):
        row.used_at = datetime.now(timezone.utc)


class _AuthLogRepository:
    def __init__(self, store: _Store) -> None:
        self.store = store

    async def create(self, **kwargs):  # noqa: ANN003
        row = _AuthLog(**kwargs)
        self.store.auth_logs.append(row)
        return row


class _SessionRepository:
    def __init__(self, store: _Store) -> None:
        self.store = store

    async def next_token_version_for_user(self, *, user_id: int) -> int:
        active_versions = [row.token_version for row in self.store.sessions.values() if row.user_id == user_id]
        return (max(active_versions) if active_versions else 0) + 1

    async def create(self, *, session_id: str, user_id: int, tenant_id: int, token_version: int, device: str | None, expires_at: datetime):
        row = _SessionRecord(
            id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            token_version=token_version,
            device=device,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )
        self.store.sessions[session_id] = row
        return row

    async def get_active(self, *, session_id: str):
        row = self.store.sessions.get(session_id)
        if row is None or row.revoked:
            return None
        return row

    async def revoke(self, row):
        row.revoked = True
        row.revoked_at = datetime.now(timezone.utc)

    async def revoke_by_id(self, *, session_id: str) -> bool:
        row = self.store.sessions.get(session_id)
        if row is None or row.revoked:
            return False
        await self.revoke(row)
        return True

    async def revoke_for_user(self, *, user_id: int) -> int:
        count = 0
        for row in self.store.sessions.values():
            if row.user_id == user_id and not row.revoked:
                row.revoked = True
                row.revoked_at = datetime.now(timezone.utc)
                count += 1
        return count

    async def list_active_for_user(self, *, user_id: int):
        return [row for row in self.store.sessions.values() if row.user_id == user_id and not row.revoked]


class _RefreshTokenRepository:
    def __init__(self, store: _Store) -> None:
        self.store = store

    async def create(
        self,
        *,
        user_id: int,
        tenant_id: int,
        token_hash: str,
        token_jti: str,
        device_info: str | None,
        ip_address: str | None,
        expires_at: datetime,
        metadata: dict,
    ):
        row = _RefreshToken(
            id=self.store.next_refresh_token_id,
            user_id=user_id,
            tenant_id=tenant_id,
            token_hash=token_hash,
            token_jti=token_jti,
            device_info=device_info,
            ip_address=ip_address,
            expires_at=expires_at,
            metadata_json=metadata,
            created_at=datetime.now(timezone.utc),
        )
        self.store.next_refresh_token_id += 1
        self.store.refresh_tokens.append(row)
        return row

    async def get_active_by_hash(self, *, token_hash: str):
        now = datetime.now(timezone.utc)
        for row in self.store.refresh_tokens:
            if row.token_hash == token_hash and not row.is_revoked and row.expires_at > now:
                return row
        return None

    async def revoke(self, row):
        row.is_revoked = True
        row.revoked_at = datetime.now(timezone.utc)

    async def revoke_for_user(self, *, user_id: int):
        for row in self.store.refresh_tokens:
            if row.user_id == user_id and not row.is_revoked:
                row.is_revoked = True
                row.revoked_at = datetime.now(timezone.utc)
        return None


class _TokenBlacklistRepository:
    def __init__(self, store: _Store) -> None:
        self.store = store

    async def add(self, *, token_jti: str, user_id: int | None, tenant_id: int | None, token_type: str, expires_at: datetime | None):
        row = _TokenBlacklist(
            token_jti=token_jti,
            user_id=user_id,
            tenant_id=tenant_id,
            token_type=token_type,
            expires_at=expires_at,
        )
        self.store.token_blacklist.append(row)
        return row


def _build_auth_service(store: _Store) -> AuthService:
    auth_service_module.hash_password = _fast_hash_password
    auth_service_module.verify_password = _fast_verify_password
    session = _FakeSession()
    service = AuthService(session)

    user_repository = _UserRepository(store)
    user_tenant_role_repository = _UserTenantRoleRepository(store)
    auth_token_repository = _AuthTokenRepository(store)
    auth_log_repository = _AuthLogRepository(store)
    refresh_token_repository = _RefreshTokenRepository(store)
    session_repository = _SessionRepository(store)
    tenant_repository = _TenantRepository(store)
    token_blacklist_repository = _TokenBlacklistRepository(store)

    service.user_repository = user_repository
    service.user_tenant_role_repository = user_tenant_role_repository
    service.auth_token_repository = auth_token_repository
    service.auth_log_repository = auth_log_repository
    service.refresh_token_repository = refresh_token_repository
    service.session_repository = session_repository
    service.refresh_session_repository = session_repository
    service.tenant_repository = tenant_repository
    service.token_blacklist_repository = token_blacklist_repository
    service.token_service = TokenService(refresh_token_repository)
    service.session_service = SessionService(
        session_repository=session_repository,
        refresh_token_repository=refresh_token_repository,
        token_blacklist_repository=token_blacklist_repository,
        token_service=service.token_service,
    )
    service.audit_log_service = _DummyAuditLogService()
    service.email_service = _DummyEmailService()

    async def _fake_enqueue_email(payload, background_tasks=None):  # noqa: ANN001
        _ = background_tasks
        return await service.email_service.send(payload)

    service._enqueue_email = _fake_enqueue_email  # type: ignore[method-assign]
    return service


def _build_user_service(store: _Store) -> UserService:
    session = _FakeSession()
    service = UserService(session)
    service.repository = _UserRepository(store)
    service.tenant_repository = _TenantRepository(store)
    return service


@pytest.mark.asyncio
async def test_register_persists_user_and_verification_token():
    store = _Store()
    service = _build_auth_service(store)

    user = await service.register(
        email="learner@example.com",
        password="StrongPass1!",
        role=UserRole.independent_learner,
        full_name="Solo Learner",
    )

    saved_user = await service.user_repository.get_by_email("learner@example.com", tenant_id=user.tenant_id)
    assert saved_user is not None
    assert saved_user.id == user.id
    assert user.tenant_id != 1
    assert store.tenants[user.tenant_id].type == TenantType.personal
    assert saved_user.full_name == "Solo Learner"
    assert saved_user.is_email_verified is False
    assert saved_user.is_profile_completed is False
    assert _fast_verify_password("StrongPass1!", saved_user.password_hash)
    assert len(store.auth_tokens) == 1
    assert store.auth_tokens[0].user_id == user.id


@pytest.mark.asyncio
async def test_independent_learner_login_can_resolve_personal_tenant_without_explicit_context():
    store = _Store()
    service = _build_auth_service(store)

    user = await service.register(
        email="solo@example.com",
        password="StrongPass1!",
        role=UserRole.independent_learner,
        full_name="Solo Learner",
    )
    token = await service.request_email_verification(tenant_id=user.tenant_id, email="solo@example.com")
    await service.verify_email(token=token)
    user.is_profile_completed = True

    result = await service.login("solo@example.com", "StrongPass1!")

    assert result.user.id == user.id
    assert result.effective_role == UserRole.independent_learner


@pytest.mark.asyncio
async def test_login_fails_before_email_verification():
    store = _Store()
    service = _build_auth_service(store)
    await service.register(email="student@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)

    with pytest.raises(UnauthorizedError, match="Email not verified"):
        await service.login("student@example.com", "StrongPass1!", tenant_id=2)


@pytest.mark.asyncio
async def test_login_requires_profile_completion_after_email_verification():
    store = _Store()
    service = _build_auth_service(store)
    await service.register(email="profile@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)

    token = await service.request_email_verification(tenant_id=2, email="profile@example.com")
    await service.verify_email(token=token)

    result = await service.login("profile@example.com", "StrongPass1!", tenant_id=2)

    assert result.requires_profile_completion is True
    assert result.access_token is not None
    assert result.refresh_token is None
    assert result.scope == "onboarding"


@pytest.mark.asyncio
async def test_profile_update_success_marks_completion():
    store = _Store()
    auth_service = _build_auth_service(store)
    user_service = _build_user_service(store)
    user = await auth_service.register(email="complete@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)

    completed = await user_service.complete_profile(
        user_id=int(user.id),
        tenant_id=2,
        full_name="Completed Student",
        phone_number="+14155550123",
        linkedin_url="https://www.linkedin.com/in/completed-student/",
        college_name="Demo University",
    )

    assert completed.is_profile_completed is True
    assert completed.phone_number == "+14155550123"
    assert completed.linkedin_url == "https://www.linkedin.com/in/completed-student/"


@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow():
    store = _Store()
    service = _build_auth_service(store)
    await service.register(email="reset@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)

    token = await service.request_password_reset(tenant_id=2, email="reset@example.com")
    user = await service.reset_password(token=token, password="NewStrong1!")

    assert _fast_verify_password("NewStrong1!", user.password_hash)
    with pytest.raises(ValidationError, match="Invalid reset token"):
        await service.reset_password(token=token, password="AnotherStrong1!")


@pytest.mark.asyncio
async def test_refresh_and_logout_revoke_tokens_and_blacklist_access_token():
    store = _Store()
    service = _build_auth_service(store)
    await service.register(email="active@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)
    verification_token = await service.request_email_verification(tenant_id=2, email="active@example.com")
    await service.verify_email(token=verification_token)
    user_service = _build_user_service(store)
    active_user = await service.user_repository.get_by_email("active@example.com", tenant_id=2)
    await user_service.complete_profile(
        user_id=int(active_user.id),
        tenant_id=2,
        full_name="Active Student",
        phone_number="+14155550123",
        linkedin_url="https://www.linkedin.com/in/active-student/",
        college_name="Demo University",
    )

    login_result = await service.login("active@example.com", "StrongPass1!", tenant_id=2, device="pytest", ip_address="127.0.0.1")
    assert login_result.refresh_token is not None
    access_token = login_result.access_token
    refresh_token = login_result.refresh_token

    next_access_token, next_refresh_token, _, _ = await service.refresh_session(
        refresh_token,
        device="pytest",
        ip_address="127.0.0.1",
    )
    assert next_access_token != access_token
    assert next_refresh_token != refresh_token

    await service.logout(next_refresh_token, access_token=next_access_token)

    assert len(store.token_blacklist) == 1
    assert any(row.is_revoked for row in store.refresh_tokens)


@pytest.mark.asyncio
async def test_account_locks_after_five_failed_logins():
    store = _Store()
    service = _build_auth_service(store)
    user = await service.register(email="locked@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)
    verification_token = await service.request_email_verification(tenant_id=2, email="locked@example.com")
    await service.verify_email(token=verification_token)
    user.is_profile_completed = True

    for _ in range(5):
        with pytest.raises(UnauthorizedError):
            await service.login("locked@example.com", "WrongPass1!", tenant_id=2)

    with pytest.raises(UnauthorizedError, match="Account locked"):
        await service.login("locked@example.com", "StrongPass1!", tenant_id=2)


@pytest.mark.asyncio
async def test_phone_otp_marks_phone_verified_and_logs_event():
    store = _Store()
    service = _build_auth_service(store)
    user = await service.register(email="otp@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)
    code = await service.send_phone_otp(user_id=int(user.id), tenant_id=2, phone_number="+14155550124")
    assert code == "123456"

    verified_user = await service.verify_phone_otp(user_id=int(user.id), tenant_id=2, code="123456")
    assert verified_user.is_phone_verified is True

    phone_otp_logs = [row for row in store.auth_logs if row.event_type == "phone_otp"]
    assert len(phone_otp_logs) == 2
    assert {row.status for row in phone_otp_logs} == {"issued", "verified"}
