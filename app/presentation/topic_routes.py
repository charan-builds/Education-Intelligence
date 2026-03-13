from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.topic_service import TopicService
from app.core.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.schemas.topic_schema import TopicDetailResponse

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/{topic_id}", response_model=TopicDetailResponse)
async def get_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(get_current_user),
):
    return await TopicService(db).get_topic_detail(topic_id)
