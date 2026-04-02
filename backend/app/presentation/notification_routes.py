from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.notification_service import NotificationService
from app.core.dependencies import get_current_user, require_roles
from app.infrastructure.database import get_db_session
from app.schemas.notification_schema import NotificationListResponse, NotificationReadResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    notifications = await NotificationService(db).list_for_user(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
    )
    return {"notifications": notifications}


@router.post("/{notification_id}/read", response_model=NotificationReadResponse)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    try:
        return await NotificationService(db).mark_read(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            notification_id=notification_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/generate")
async def generate_notifications(
    limit_users: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    created = await NotificationService(db).generate_due_notifications(
        tenant_id=current_user.tenant_id,
        limit_users=limit_users,
    )
    await db.commit()
    return {"tenant_id": current_user.tenant_id, "created": created}
