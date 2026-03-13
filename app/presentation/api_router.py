from fastapi import APIRouter

from app.presentation.audit_routes import router as audit_router
from app.presentation.auth_routes import router as auth_router
from app.presentation.diagnostic_routes import router as diagnostic_router
from app.presentation.feature_flag_routes import router as feature_flag_router
from app.presentation.goal_routes import router as goal_router
from app.presentation.mentor_routes import router as mentor_router
from app.presentation.outbox_routes import router as outbox_router
from app.presentation.roadmap_routes import router as roadmap_router
from app.presentation.tenant_routes import router as tenant_router
from app.presentation.topic_routes import router as topic_router
from app.presentation.user_routes import router as user_router

api_router = APIRouter()
api_router.include_router(audit_router)
api_router.include_router(auth_router)
api_router.include_router(tenant_router)
api_router.include_router(user_router)
api_router.include_router(goal_router)
api_router.include_router(topic_router)
api_router.include_router(mentor_router)
api_router.include_router(feature_flag_router)
api_router.include_router(diagnostic_router)
api_router.include_router(roadmap_router)
api_router.include_router(outbox_router)
