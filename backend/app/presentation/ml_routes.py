from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ml_platform_service import MLPlatformService
from app.core.dependencies import get_current_user, require_roles
from app.infrastructure.database import get_db_session
from app.schemas.ml_schema import (
    DifficultyInferenceResponse,
    DropoutInferenceResponse,
    LearnerFeatureSnapshotResponse,
    MLOutputOverviewResponse,
    MLTrainingRunResponse,
    ModelTrainRequest,
    RecommendationInferenceResponse,
)

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/overview", response_model=MLOutputOverviewResponse)
async def ml_overview(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return MLOutputOverviewResponse(**(await MLPlatformService(db).overview(user_id=current_user.id, tenant_id=current_user.tenant_id)))


@router.post("/features/snapshot", response_model=LearnerFeatureSnapshotResponse)
async def create_feature_snapshot(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return LearnerFeatureSnapshotResponse(**(
        await MLPlatformService(db).build_feature_snapshot(user_id=current_user.id, tenant_id=current_user.tenant_id)
    ))


@router.post("/train", response_model=MLTrainingRunResponse)
async def train_model(
    payload: ModelTrainRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    return MLTrainingRunResponse(**(
        await MLPlatformService(db).train_model(tenant_id=current_user.tenant_id, model_name=payload.model_name)
    ))


@router.get("/infer/recommendations", response_model=RecommendationInferenceResponse)
async def infer_recommendations(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return RecommendationInferenceResponse(**(
        await MLPlatformService(db).recommend_topics(user_id=current_user.id, tenant_id=current_user.tenant_id)
    ))


@router.get("/infer/difficulty/{topic_id}", response_model=DifficultyInferenceResponse)
async def infer_topic_difficulty(
    topic_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return DifficultyInferenceResponse(**(
        await MLPlatformService(db).predict_topic_difficulty(tenant_id=current_user.tenant_id, topic_id=topic_id)
    ))


@router.get("/infer/dropout", response_model=DropoutInferenceResponse)
async def infer_dropout_risk(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return DropoutInferenceResponse(**(
        await MLPlatformService(db).predict_dropout_risk(user_id=current_user.id, tenant_id=current_user.tenant_id)
    ))
