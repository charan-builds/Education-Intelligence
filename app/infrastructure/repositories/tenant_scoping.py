from sqlalchemy.sql.elements import ColumnElement


# Central helper to keep tenant-bound filters consistent across repositories.
def tenant_user_scope(user_relationship, tenant_id: int) -> ColumnElement[bool]:
    return user_relationship.has(tenant_id=tenant_id)
