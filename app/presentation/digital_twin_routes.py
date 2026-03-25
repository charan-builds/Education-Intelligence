from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.digital_twin_service import DigitalTwinService
from app.core.dependencies import require_roles
from app.infrastructure.database import get_db_session
from app.schemas.digital_twin_schema import DigitalTwinResponse

router = APIRouter(prefix="/digital-twin", tags=["digital-twin"])


@router.get("", response_model=DigitalTwinResponse)
async def get_digital_twin(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("student")),
):
    return await DigitalTwinService(db).get_twin(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
