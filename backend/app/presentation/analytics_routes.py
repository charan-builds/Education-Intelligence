import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.analytics_service import AnalyticsService
from app.application.services.analytics_snapshot_service import AnalyticsSnapshotService
from app.application.services.precomputed_analytics_service import PrecomputedAnalyticsService
from app.application.services.skill_vector_service import SkillVectorService
from app.core.dependencies import get_current_user
from app.core.dependencies import get_pagination_params, require_roles
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.database import get_db_session
from app.infrastructure.jobs.dispatcher import enqueue_job_with_options
from app.infrastructure.repositories.dead_letter_repository import DeadLetterRepository
from app.schemas.common_schema import PaginationParams
from app.schemas.analytics_schema import (
    AnalyticsOverviewResponse,
    LearnerIntelligenceOverviewResponse,
    LearnerSkillVectorResponse,
    LearningTrendPointResponse,
    PlatformAnalyticsOverviewResponse,
    RetentionAnalyticsResponse,
    RoadmapProgressSummaryResponse,
    StudentPerformanceAnalyticsResponse,
    TopicPerformanceAnalyticsResponse,
    WeakTopicInsightResponse,
    TopicMasteryAnalyticsResponse,
)
from app.application.services.retention_service import RetentionService

router = APIRouter(prefix="/analytics", tags=["analytics"])
STALE_SNAPSHOT_THRESHOLD = timedelta(minutes=5)


def _dead_letter_tenant_scope(current_user) -> int | None:
    role = getattr(getattr(current_user, "role", None), "value", getattr(current_user, "role", None))
    return None if role == "super_admin" else int(current_user.tenant_id)


def _snapshot_meta(*, status: str, last_updated: str | None, estimated_time: int | None = None) -> dict:
    return {
        "status": status,
        "last_updated": last_updated,
        "is_rebuilding": status == "pending",
        "estimated_time": estimated_time if status == "pending" else None,
    }


def _snapshot_status(last_updated: str | None) -> str:
    if not last_updated:
        return "pending"
    try:
        parsed = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
    except ValueError:
        return "ready"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)
    return "stale" if age > STALE_SNAPSHOT_THRESHOLD else "ready"


async def _enqueue_high_priority_snapshot_rebuild(*, tenant_id: int, snapshot_type: str) -> bool:
    from app.infrastructure.jobs.tasks import enqueue_snapshot_rebuild

    return await enqueue_snapshot_rebuild(
        tenant_id=int(tenant_id),
        snapshot_type=str(snapshot_type),
        priority=9,
    )


async def _enqueue_deduplicated_analytics_job(*, task_name: str, lock_key: str, kwargs: dict, ttl_seconds: int = 300) -> bool:
    cache = CacheService()
    token = await cache.acquire_lock(lock_key, ttl=ttl_seconds)
    if token is None:
        return False
    job_kwargs = {**kwargs, "dispatch_lock_key": lock_key, "dispatch_lock_token": token}
    queued = enqueue_job_with_options(task_name, kwargs=job_kwargs)
    if not queued:
        await cache.release_lock(lock_key, token)
        return False
    return True


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    payload = await AnalyticsService(db).aggregated_metrics(current_user.tenant_id)
    if payload.get("meta", {}).get("status") in {"pending", "stale"}:
        if payload.get("meta", {}).get("status") == "stale":
            await _enqueue_high_priority_snapshot_rebuild(
                tenant_id=int(current_user.tenant_id),
                snapshot_type="tenant_dashboard",
            )
        else:
            enqueue_job_with_options("jobs.refresh_precomputed_analytics", kwargs={"tenant_id": int(current_user.tenant_id)})
    return payload


@router.get("/roadmap-progress", response_model=RoadmapProgressSummaryResponse)
async def get_roadmap_progress_analytics(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    payload = await AnalyticsService(db).roadmap_progress_summary(
        current_user.tenant_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    snapshot_meta = payload.get("snapshot_meta") or {}
    if snapshot_meta.get("status") in {"pending", "stale"}:
        if snapshot_meta.get("status") == "stale":
            await _enqueue_high_priority_snapshot_rebuild(
                tenant_id=int(current_user.tenant_id),
                snapshot_type="roadmap_progress_summary",
            )
        else:
            await _enqueue_deduplicated_analytics_job(
                task_name="jobs.refresh_roadmap_progress_summary",
                lock_key=f"analytics:roadmap-progress:{int(current_user.tenant_id)}",
                kwargs={"tenant_id": int(current_user.tenant_id)},
            )
    return payload


@router.get("/topic-mastery", response_model=TopicMasteryAnalyticsResponse)
async def get_topic_mastery_analytics(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    payload = await AnalyticsService(db).topic_mastery_summary(current_user.tenant_id)
    if payload.get("meta", {}).get("status") in {"pending", "stale"}:
        if payload.get("meta", {}).get("status") == "stale":
            await _enqueue_high_priority_snapshot_rebuild(
                tenant_id=int(current_user.tenant_id),
                snapshot_type="tenant_dashboard",
            )
        else:
            enqueue_job_with_options("jobs.refresh_precomputed_analytics", kwargs={"tenant_id": int(current_user.tenant_id)})
    return payload


@router.get("/platform-overview", response_model=PlatformAnalyticsOverviewResponse)
async def get_platform_analytics_overview(
    db: AsyncSession = Depends(get_db_session),
    _current_user=Depends(require_roles("super_admin")),
):
    return await AnalyticsService(db).platform_overview()


@router.get("/retention", response_model=RetentionAnalyticsResponse)
async def get_retention_analytics(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    snapshot = await AnalyticsSnapshotService(db).get_latest_snapshot(
        current_user.tenant_id,
        "tenant_retention_summary",
    )
    if snapshot is not None:
        payload = dict(snapshot["data"])
        last_updated = snapshot["created_at"].isoformat() if snapshot.get("created_at") else None
        status = _snapshot_status(last_updated)
        payload["meta"] = _snapshot_meta(status=status, last_updated=last_updated)
        if status == "stale":
            await _enqueue_high_priority_snapshot_rebuild(
                tenant_id=int(current_user.tenant_id),
                snapshot_type="tenant_retention_summary",
            )
        return payload
    await _enqueue_deduplicated_analytics_job(
        task_name="jobs.refresh_retention_summary",
        lock_key=f"analytics:retention:{int(current_user.tenant_id)}",
        kwargs={"tenant_id": int(current_user.tenant_id)},
    )
    return {
        "tenant_id": current_user.tenant_id,
        "due_review_count": 0,
        "retention_curve": [],
        "weak_retention_topics": [],
        "meta": _snapshot_meta(status="pending", last_updated=None, estimated_time=30),
    }


@router.get("/student-insights", response_model=LearnerIntelligenceOverviewResponse)
async def get_student_insights(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    snapshot = await AnalyticsSnapshotService(db).get_latest_snapshot(
        current_user.tenant_id,
        "learner_intelligence_overview",
        subject_id=current_user.id,
    )
    if snapshot is not None:
        payload = dict(snapshot["data"])
        last_updated = snapshot["created_at"].isoformat() if snapshot.get("created_at") else None
        status = _snapshot_status(last_updated)
        payload["meta"] = _snapshot_meta(status=status, last_updated=last_updated)
        if status == "stale":
            await _enqueue_deduplicated_analytics_job(
                task_name="jobs.refresh_learner_intelligence_overview",
                lock_key=f"analytics:learner-intelligence:{int(current_user.id)}",
                kwargs={"tenant_id": int(current_user.tenant_id), "user_id": int(current_user.id)},
            )
        return payload
    await _enqueue_deduplicated_analytics_job(
        task_name="jobs.refresh_learner_intelligence_overview",
        lock_key=f"analytics:learner-intelligence:{int(current_user.id)}",
        kwargs={"tenant_id": int(current_user.tenant_id), "user_id": int(current_user.id)},
    )
    return {
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id,
        "mastery_avg": 0.0,
        "confidence_avg": 0.0,
        "learning_speed_seconds": 0.0,
        "retry_count": 0,
        "tracked_topics": 0,
        "meta": _snapshot_meta(status="pending", last_updated=None, estimated_time=30),
    }


@router.get("/skill-vectors", response_model=LearnerSkillVectorResponse)
async def get_skill_vectors(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    vectors = await SkillVectorService(db).learner_vectors(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    return {
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id,
        "vectors": vectors,
    }


@router.get("/weak-topics", response_model=list[WeakTopicInsightResponse])
async def get_weak_topics(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    return await SkillVectorService(db).weak_topics(tenant_id=current_user.tenant_id)


@router.get("/learning-trends", response_model=list[LearningTrendPointResponse])
async def get_learning_trends(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    snapshot = await AnalyticsSnapshotService(db).get_latest_snapshot(
        current_user.tenant_id,
        "learning_trends",
    )
    if snapshot is not None:
        last_updated = snapshot["created_at"].isoformat() if snapshot.get("created_at") else None
        if _snapshot_status(last_updated) == "stale":
            await _enqueue_high_priority_snapshot_rebuild(
                tenant_id=int(current_user.tenant_id),
                snapshot_type="learning_trends",
            )
        return list(snapshot["data"].get("points") or [])
    await _enqueue_deduplicated_analytics_job(
        task_name="jobs.refresh_learning_trends",
        lock_key=f"analytics:learning-trends:{int(current_user.tenant_id)}",
        kwargs={"tenant_id": int(current_user.tenant_id)},
    )
    return []


@router.get("/student/{user_id}", response_model=StudentPerformanceAnalyticsResponse)
async def get_student_performance_analytics(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    service = AnalyticsService(db)
    try:
        return await service.student_performance_analytics(
            tenant_id=current_user.tenant_id,
            user_id=user_id,
        )
    except ValueError as exc:
        if str(exc) == "Student analytics snapshot not ready":
            await _enqueue_deduplicated_analytics_job(
                task_name="jobs.refresh_student_analytics",
                lock_key=f"analytics:student:{int(user_id)}",
                kwargs={"tenant_id": int(current_user.tenant_id), "user_id": int(user_id)},
            )
            return service.empty_student_performance_analytics(
                tenant_id=int(current_user.tenant_id),
                user_id=int(user_id),
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/topic/{topic_id}", response_model=TopicPerformanceAnalyticsResponse)
async def get_topic_performance_analytics(
    topic_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    service = AnalyticsService(db)
    try:
        return await service.topic_performance_analytics(
            tenant_id=current_user.tenant_id,
            topic_id=topic_id,
        )
    except ValueError as exc:
        if str(exc) == "Topic analytics snapshot not ready":
            await _enqueue_deduplicated_analytics_job(
                task_name="jobs.refresh_topic_analytics",
                lock_key=f"analytics:topic:{int(topic_id)}",
                kwargs={"tenant_id": int(current_user.tenant_id), "topic_id": int(topic_id)},
            )
            return await service.empty_topic_performance_analytics(
                tenant_id=int(current_user.tenant_id),
                topic_id=int(topic_id),
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/precomputed/tenant-dashboard")
async def get_precomputed_tenant_dashboard(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "mentor", "admin", "super_admin")),
):
    service = PrecomputedAnalyticsService(db)
    snapshot = await service.latest_tenant_dashboard(tenant_id=current_user.tenant_id)
    if snapshot is not None:
        status = _snapshot_status(snapshot.get("updated_at"))
        if status == "stale":
            await _enqueue_high_priority_snapshot_rebuild(
                tenant_id=int(current_user.tenant_id),
                snapshot_type="tenant_dashboard",
            )
        return {
            **snapshot,
            "meta": _snapshot_meta(status=status, last_updated=snapshot.get("updated_at")),
        }
    return {
        "tenant_id": current_user.tenant_id,
        "active_learners": 0,
        "weekly_event_count": 0,
        "average_topic_mastery": 0.0,
        "meta": _snapshot_meta(status="pending", last_updated=None, estimated_time=30),
    }


@router.get("/precomputed/user-learning-summary")
async def get_precomputed_user_learning_summary(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    service = PrecomputedAnalyticsService(db)
    snapshot = await service.latest_user_learning_summary(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    if snapshot is not None:
        status = _snapshot_status(snapshot.get("updated_at"))
        return {
            **snapshot,
            "meta": _snapshot_meta(status=status, last_updated=snapshot.get("updated_at")),
        }
    return {
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id,
        "weekly_event_count": 0,
        "average_score": 0.0,
        "meta": _snapshot_meta(status="pending", last_updated=None, estimated_time=30),
    }


@router.post("/precomputed/refresh")
async def refresh_precomputed_analytics(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    enqueue_job_with_options(
        "jobs.refresh_precomputed_analytics",
        kwargs={"tenant_id": int(current_user.tenant_id)},
    )
    return {"status": "queued", "tenant_id": int(current_user.tenant_id)}


@router.get("/jobs/failed")
async def list_failed_analytics_jobs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    rows = await DeadLetterRepository(db).list_recent_by_source_type(
        source_type="analytics_job",
        tenant_id=_dead_letter_tenant_scope(current_user),
        limit=limit,
    )
    return {
        "items": [
            {
                "id": int(row.id),
                "tenant_id": int(row.tenant_id) if row.tenant_id is not None else None,
                "job_name": row.event_type,
                "payload": json.loads(row.payload_json),
                "error_message": row.error_message,
                "attempts": int(row.attempts),
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.post("/jobs/failed/{dead_letter_id}/retry")
async def retry_failed_analytics_job(
    dead_letter_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    row = await DeadLetterRepository(db).get_by_id(
        dead_letter_id=dead_letter_id,
        tenant_id=_dead_letter_tenant_scope(current_user),
    )
    if row is None or row.source_type != "analytics_job":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analytics job failure not found")

    payload = json.loads(row.payload_json)
    job_name = str(row.event_type)
    if job_name == "jobs.refresh_student_analytics":
        lock_key = f"analytics:student:{int(payload['user_id'])}"
    elif job_name == "jobs.refresh_topic_analytics":
        lock_key = f"analytics:topic:{int(payload['topic_id'])}"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported analytics job type")

    queued = await _enqueue_deduplicated_analytics_job(
        task_name=job_name,
        lock_key=lock_key,
        kwargs=payload,
    )
    return {
        "status": "queued" if queued else "already_queued",
        "dead_letter_id": dead_letter_id,
        "job_name": job_name,
    }
