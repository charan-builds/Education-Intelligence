from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.models.user import User


@dataclass(frozen=True)
class AuthContext:
    user: User
    actor_user_id: int
    actor_tenant_id: int
    effective_tenant_id: int

    @property
    def id(self) -> int:
        return int(self.user.id)

    @property
    def tenant_id(self) -> int:
        return int(self.effective_tenant_id)

    @property
    def role(self):
        return self.user.role

    def __getattr__(self, item: str) -> Any:
        return getattr(self.user, item)
