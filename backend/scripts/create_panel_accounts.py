from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import select

from app.domain.models.tenant import Tenant
from app.domain.models.user import UserRole
from app.infrastructure.database import open_system_session
from seed import _ensure_user


@dataclass(frozen=True)
class AccountSpec:
    panel: str
    email: str
    password: str
    role: UserRole
    tenant_name: str
    display_name: str


ACCOUNT_SPECS: tuple[AccountSpec, ...] = (
    AccountSpec(
        panel="Student Panel",
        email="charanderangula007+student@gmail.com",
        password="PanelStudent123!",
        role=UserRole.student,
        tenant_name="Demo University",
        display_name="Charan Student",
    ),
    AccountSpec(
        panel="Teacher Panel",
        email="charanderangula007+teacher@gmail.com",
        password="PanelTeacher123!",
        role=UserRole.teacher,
        tenant_name="Demo University",
        display_name="Charan Teacher",
    ),
    AccountSpec(
        panel="Mentor Panel",
        email="charanderangula007+mentor@gmail.com",
        password="PanelMentor123!",
        role=UserRole.mentor,
        tenant_name="Demo University",
        display_name="Charan Mentor",
    ),
    AccountSpec(
        panel="Admin Panel",
        email="charanderangula007+admin@gmail.com",
        password="PanelAdmin123!",
        role=UserRole.admin,
        tenant_name="Demo University",
        display_name="Charan Admin",
    ),
    AccountSpec(
        panel="Super Admin Panel",
        email="charanderangula007+superadmin@gmail.com",
        password="PanelSuperAdmin123!",
        role=UserRole.super_admin,
        tenant_name="Platform",
        display_name="Charan Super Admin",
    ),
)


async def main() -> None:
    async with open_system_session() as session:
        tenants = {
            tenant.name: tenant
            for tenant in (
                await session.execute(
                    select(Tenant).where(Tenant.name.in_({spec.tenant_name for spec in ACCOUNT_SPECS}))
                )
            )
            .scalars()
            .all()
        }

        missing = sorted({spec.tenant_name for spec in ACCOUNT_SPECS} - set(tenants))
        if missing:
            raise RuntimeError(f"Missing tenants: {', '.join(missing)}")

        for spec in ACCOUNT_SPECS:
            tenant = tenants[spec.tenant_name]
            user = await _ensure_user(
                session,
                tenant=tenant,
                email=spec.email,
                password=spec.password,
                role=spec.role,
                display_name=spec.display_name,
            )
            print(
                f"{spec.panel}: id={user.id} email={spec.email} password={spec.password} "
                f"tenant_id={tenant.id} tenant={tenant.name}"
            )

        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
