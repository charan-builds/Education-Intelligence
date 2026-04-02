from sqlalchemy import or_
from sqlalchemy.sql.elements import ColumnElement

from app.domain.models.user import User
from app.domain.models.user_tenant_role import UserTenantRole


# Central helper to keep tenant-bound filters consistent across repositories.
def tenant_user_scope(user_relationship, tenant_id: int) -> ColumnElement[bool]:
    return user_relationship.has(
        or_(
            User.tenant_id == tenant_id,
            User.tenant_roles.any(UserTenantRole.tenant_id == tenant_id),
        )
    )


def user_belongs_to_tenant(user_model, tenant_id: int) -> ColumnElement[bool]:
    return or_(
        user_model.tenant_id == tenant_id,
        user_model.tenant_roles.any(UserTenantRole.tenant_id == tenant_id),
    )


def user_has_tenant_role(user_model, tenant_id: int, *roles: str) -> ColumnElement[bool]:
    if not roles:
        return user_belongs_to_tenant(user_model, tenant_id)
    return or_(
        (user_model.tenant_id == tenant_id) & (user_model.role.in_(roles)),
        user_model.tenant_roles.any(
            (UserTenantRole.tenant_id == tenant_id) & (UserTenantRole.role.in_(roles))
        ),
    )
