from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.search_service import SearchService
from app.core.authorization import require_permission
from app.infrastructure.database import get_db_session

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_permission("search:query")),
):
    return await SearchService(db).search(tenant_id=current_user.tenant_id, query=q, limit=limit)
