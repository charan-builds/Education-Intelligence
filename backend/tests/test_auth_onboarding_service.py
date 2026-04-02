from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.domain.models  # noqa: F401
from app.application.exceptions import UnauthorizedError, ValidationError
from app.application.services.auth_service import AuthService
from app.application.services.user_service import UserService
from app.core.security import verify_password
from app.domain.models.auth_token import AuthToken
from app.domain.models.auth_log import AuthLog
from app.domain.models.base import Base
from app.domain.models.refresh_token import RefreshToken
from app.domain.models.session import SessionRecord
from app.domain.models.tenant import Tenant, TenantType
from app.domain.models.token_blacklist import TokenBlacklist
from app.domain.models.user import User, UserRole
from app.domain.models.user_tenant_role import UserTenantRole


class _DummyAuditLogService:
    async def record(self, **kwargs):  # noqa: ANN003
        return kwargs


class _DummyEmailService:
    def build_verification_email(self, *, to_email: str, verification_url: str):
        return type("Payload", (), {"to_email": to_email, "subject": "verify", "html_content": verification_url, "text_content": verification_url})()

    def build_password_reset_email(self, *, to_email: str, reset_url: str):
        return type("Payload", (), {"to_email": to_email, "subject": "reset", "html_content": reset_url, "text_content": reset_url})()

    async def send(self, payload):  # noqa: ANN001
        return {"delivered": True, "to_email": payload.to_email}


def _build_auth_service(session: AsyncSession) -> AuthService:
    service = AuthService(session)
    service.audit_log_service = _DummyAuditLogService()
    service.email_service = _DummyEmailService()
    async def _fake_enqueue_email(payload, background_tasks=None):  # noqa: ANN001
        _ = background_tasks
        return await service.email_service.send(payload)

    service._enqueue_email = _fake_enqueue_email  # type: ignore[method-assign]
    return service


async def _run_with_db(assertions):  # noqa: ANN001
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    Tenant.__table__,
                    User.__table__,
                    UserTenantRole.__table__,
                    SessionRecord.__table__,
                    AuthToken.__table__,
                    AuthLog.__table__,
                    RefreshToken.__table__,
                    TokenBlacklist.__table__,
                ],
            )
        )

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        session.add(Tenant(id=1, name="Platform", subdomain="platform", type=TenantType.platform, created_at=datetime.now(timezone.utc)))
        session.add(Tenant(id=2, name="Demo University", subdomain="demo", type=TenantType.college, created_at=datetime.now(timezone.utc)))
        await session.commit()
        await assertions(session)
    await engine.dispose()


@pytest.mark.asyncio
async def test_register_persists_user_and_verification_token():
    async def scenario(session: AsyncSession) -> None:
        service = _build_auth_service(session)

        user = await service.register(
            email="learner@example.com",
            password="StrongPass1!",
            role=UserRole.independent_learner,
            full_name="Solo Learner",
        )

        saved_user = await service.user_repository.get_by_email("learner@example.com")
        assert saved_user is not None
        assert saved_user.id == user.id
        assert saved_user.full_name == "Solo Learner"
        assert saved_user.is_email_verified is False
        assert saved_user.is_profile_completed is False
        assert verify_password("StrongPass1!", saved_user.password_hash)

        token_rows = (await session.execute(sa.select(AuthToken))).scalars().all()
        assert len(token_rows) == 1
        assert token_rows[0].user_id == user.id

    await _run_with_db(scenario)


@pytest.mark.asyncio
async def test_login_fails_before_email_verification():
    async def scenario(session: AsyncSession) -> None:
        service = _build_auth_service(session)
        await service.register(email="student@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)

        with pytest.raises(UnauthorizedError, match="Email not verified"):
            await service.login("student@example.com", "StrongPass1!", tenant_id=2)

    await _run_with_db(scenario)


@pytest.mark.asyncio
async def test_login_requires_profile_completion_after_email_verification():
    async def scenario(session: AsyncSession) -> None:
        service = _build_auth_service(session)
        await service.register(email="profile@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)

        token = await service.request_email_verification(tenant_id=2, email="profile@example.com")
        await service.verify_email(token=token)

        result = await service.login("profile@example.com", "StrongPass1!", tenant_id=2)

        assert result.requires_profile_completion is True
        assert result.access_token is not None
        assert result.refresh_token is None
        assert result.scope == "onboarding"

    await _run_with_db(scenario)


@pytest.mark.asyncio
async def test_profile_update_success_marks_completion():
    async def scenario(session: AsyncSession) -> None:
        auth_service = _build_auth_service(session)
        user_service = UserService(session)
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

    await _run_with_db(scenario)


@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow():
    async def scenario(session: AsyncSession) -> None:
        service = _build_auth_service(session)
        await service.register(email="reset@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)

        token = await service.request_password_reset(tenant_id=2, email="reset@example.com")
        user = await service.reset_password(token=token, password="NewStrong1!")

        assert verify_password("NewStrong1!", user.password_hash)
        with pytest.raises(ValidationError, match="Invalid reset token"):
            await service.reset_password(token=token, password="AnotherStrong1!")

    await _run_with_db(scenario)


@pytest.mark.asyncio
async def test_refresh_and_logout_revoke_tokens_and_blacklist_access_token():
    async def scenario(session: AsyncSession) -> None:
        service = _build_auth_service(session)
        await service.register(email="active@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)
        verification_token = await service.request_email_verification(tenant_id=2, email="active@example.com")
        await service.verify_email(token=verification_token)
        user_service = UserService(session)
        await user_service.complete_profile(
            user_id=int((await service.user_repository.get_by_email("active@example.com", tenant_id=2)).id),
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

        blacklisted = (await session.execute(sa.select(TokenBlacklist))).scalars().all()
        refresh_rows = (await session.execute(sa.select(RefreshToken))).scalars().all()
        assert len(blacklisted) == 1
        assert any(row.is_revoked for row in refresh_rows)

    await _run_with_db(scenario)


@pytest.mark.asyncio
async def test_account_locks_after_five_failed_logins():
    async def scenario(session: AsyncSession) -> None:
        service = _build_auth_service(session)
        user = await service.register(email="locked@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)
        verification_token = await service.request_email_verification(tenant_id=2, email="locked@example.com")
        await service.verify_email(token=verification_token)
        user.is_profile_completed = True
        await session.commit()

        for _ in range(5):
            with pytest.raises(UnauthorizedError):
                await service.login("locked@example.com", "WrongPass1!", tenant_id=2)

        with pytest.raises(UnauthorizedError, match="Account locked"):
            await service.login("locked@example.com", "StrongPass1!", tenant_id=2)

    await _run_with_db(scenario)


@pytest.mark.asyncio
async def test_phone_otp_marks_phone_verified_and_logs_event():
    async def scenario(session: AsyncSession) -> None:
        service = _build_auth_service(session)
        user = await service.register(email="otp@example.com", password="StrongPass1!", tenant_id=2, role=UserRole.student)
        code = await service.send_phone_otp(user_id=int(user.id), tenant_id=2, phone_number="+14155550124")
        assert code == "123456"

        verified_user = await service.verify_phone_otp(user_id=int(user.id), tenant_id=2, code="123456")
        assert verified_user.is_phone_verified is True

        auth_logs = (await session.execute(sa.select(AuthLog).where(AuthLog.event_type == "phone_otp"))).scalars().all()
        assert len(auth_logs) == 2
        assert {row.status for row in auth_logs} == {"issued", "verified"}

    await _run_with_db(scenario)
