from fastapi import APIRouter

from app.presentation.ai_routes import router as ai_router
from app.presentation.analytics_routes import router as analytics_router
from app.presentation.audit_routes import router as audit_router
from app.presentation.auth_routes import router as auth_router
from app.presentation.community_routes import router as community_router
from app.presentation.content_routes import router as content_router
from app.presentation.career_routes import router as career_router
from app.presentation.dashboard_routes import router as dashboard_router
from app.presentation.digital_twin_routes import router as digital_twin_router
from app.presentation.diagnostic_routes import router as diagnostic_router
from app.presentation.ecosystem_routes import router as ecosystem_router
from app.presentation.feature_flag_routes import router as feature_flag_router
from app.presentation.file_routes import router as file_router
from app.presentation.goal_routes import router as goal_router
from app.presentation.gamification_routes import router as gamification_router
from app.presentation.mentor_routes import router as mentor_router
from app.presentation.ml_routes import router as ml_router
from app.presentation.notification_routes import router as notification_router
from app.presentation.outbox_routes import router as outbox_router
from app.presentation.realtime_routes import router as realtime_router
from app.presentation.revision_routes import router as revision_router
from app.presentation.roadmap_routes import router as roadmap_router
from app.presentation.social_routes import router as social_router
from app.presentation.search_routes import router as search_router
from app.presentation.test_routes import router as test_router
from app.presentation.tenant_routes import router as tenant_router
from app.presentation.topic_routes import router as topic_router
from app.presentation.user_routes import router as user_router

api_router = APIRouter()
api_router.include_router(ai_router)
api_router.include_router(analytics_router)
api_router.include_router(audit_router)
api_router.include_router(auth_router)
api_router.include_router(community_router)
api_router.include_router(content_router)
api_router.include_router(career_router)
api_router.include_router(dashboard_router)
api_router.include_router(digital_twin_router)
api_router.include_router(tenant_router)
api_router.include_router(user_router)
api_router.include_router(goal_router)
api_router.include_router(gamification_router)
api_router.include_router(topic_router)
api_router.include_router(mentor_router)
api_router.include_router(ml_router)
api_router.include_router(notification_router)
api_router.include_router(feature_flag_router)
api_router.include_router(file_router)
api_router.include_router(diagnostic_router)
api_router.include_router(roadmap_router)
api_router.include_router(revision_router)
api_router.include_router(social_router)
api_router.include_router(search_router)
api_router.include_router(test_router)
api_router.include_router(outbox_router)
api_router.include_router(realtime_router)
api_router.include_router(ecosystem_router)
