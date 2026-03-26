from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.exceptions import UnauthorizedError
from app.domain.models.user import User
from app.domain.models.user import UserRole
from app.infrastructure.repositories.user_tenant_role_repository import UserTenantRoleRepository


@dataclass(frozen=True)
class AuthContext:
    user: User
    actor_user_id: int
    actor_tenant_id: int
    effective_tenant_id: int
    membership_role: UserRole

    @property
    def id(self) -> int:
        return int(self.user.id)

    @property
    def tenant_id(self) -> int:
        return int(self.effective_tenant_id)

    @property
    def role(self):
        return self.membership_role

    def __getattr__(self, item: str) -> Any:
        return getattr(self.user, item)


async def validate_tenant_membership(user_id: int, tenant_id: int, db_session) -> None:
    membership = await UserTenantRoleRepository(db_session).get_membership(user_id=user_id, tenant_id=tenant_id)
    if membership is None:
        raise UnauthorizedError("User is not a member of the specified tenant")
