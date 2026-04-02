from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_context import AuthContext
from app.core.dependencies import get_current_user
from app.domain.models.authorization_policy import AuthorizationPolicy
from app.domain.models.user import UserRole
from app.infrastructure.database import get_db_session


ROLE_PERMISSIONS: dict[str, set[str]] = {
    UserRole.super_admin.value: {"*"},
    UserRole.admin.value: {
        "feature_flags:read",
        "feature_flags:update",
        "audit_logs:read",
        "search:query",
        "files:upload",
    },
    UserRole.teacher.value: {"analytics:read", "search:query"},
    UserRole.mentor.value: {"analytics:read", "search:query"},
    UserRole.student.value: {"search:query", "files:upload"},
}


class AuthorizationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_allowed(
        self,
        *,
        user: AuthContext,
        permission: str,
        resource_owner_user_id: int | None = None,
        attributes: dict | None = None,
    ) -> bool:
        role_permissions = ROLE_PERMISSIONS.get(user.role.value, set())
        if "*" in role_permissions or permission in role_permissions:
            if resource_owner_user_id is None or int(resource_owner_user_id) == int(user.id):
                return True
            if user.role.value in {UserRole.admin.value, UserRole.super_admin.value}:
                return True

        resource, action = permission.split(":", 1)
        policies = (
            await self.session.execute(
                select(AuthorizationPolicy).where(
                    AuthorizationPolicy.enabled.is_(True),
                    AuthorizationPolicy.resource == resource,
                    AuthorizationPolicy.action == action,
                    AuthorizationPolicy.subject.in_([user.role.value, f"user:{user.id}"]),
                    AuthorizationPolicy.tenant_id.in_([user.tenant_id, None]),
                )
            )
        ).scalars().all()
        for policy in policies:
            conditions = json.loads(policy.conditions_json or "{}")
            if self._matches_conditions(
                conditions=conditions,
                user=user,
                resource_owner_user_id=resource_owner_user_id,
                attributes=attributes or {},
            ):
                return policy.effect == "allow"
        return False

    @staticmethod
    def _matches_conditions(
        *,
        conditions: dict,
        user: AuthContext,
        resource_owner_user_id: int | None,
        attributes: dict,
    ) -> bool:
        if conditions.get("owner_only") and resource_owner_user_id is not None and int(resource_owner_user_id) != int(user.id):
            return False
        if "tenant_equals" in conditions and int(conditions["tenant_equals"]) != int(user.tenant_id):
            return False
        required_attrs = conditions.get("attributes", {})
        for key, expected in required_attrs.items():
            if attributes.get(key) != expected:
                return False
        return True


def require_permission(permission: str, *, resource_owner_user_id: int | None = None):
    async def _require(
        user: AuthContext = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session),
    ) -> AuthContext:
        allowed = await AuthorizationService(db).is_allowed(
            user=user,
            permission=permission,
            resource_owner_user_id=resource_owner_user_id,
        )
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _require
