from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.tenant_service import TenantService
from app.core.dependencies import get_pagination_params, require_roles
from app.infrastructure.database import get_db_session
from app.schemas.common_schema import PaginationParams
from app.schemas.tenant_schema import TenantCreateRequest, TenantPageResponse, TenantResponse

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse)
async def create_tenant(
    payload: TenantCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles("super_admin")),
):
    service = TenantService(db)
    return await service.create_tenant(payload.name, payload.type)


@router.get("", response_model=TenantPageResponse)
async def list_tenants(
    db: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles("super_admin")),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await TenantService(db).list_tenants_page(
        limit=pagination.limit,
        offset=pagination.offset,
        cursor=pagination.cursor,
    )
