# Project Overview

This file gives a clear summary of the project structure, important modules, small code snippets, technologies used, and the main system flow.

## a) Project Structure

### Complete Repository Structure

```text
intelligentSystems/
├── README.md
├── PROJECT_OVERVIEW.md
├── FOLDER_STRUCTURE.md
├── blueprint.md
├── independentlearnerblueprint.md
├── TODO.md
├── Makefile
├── docker-compose.yml
├── run_workers.sh
│
├── backend/                                   # Main FastAPI backend
│   ├── README.md
│   ├── pyproject.toml
│   ├── alembic/                               # Migration config and versions
│   ├── app/
│   │   ├── main.py                            # FastAPI entrypoint
│   │   ├── application/
│   │   │   ├── domains/                       # Domain grouping modules
│   │   │   │   ├── analytics/
│   │   │   │   ├── community/
│   │   │   │   ├── learning/
│   │   │   │   └── ml/
│   │   │   ├── exceptions.py
│   │   │   └── services/                      # Core business services
│   │   │       ├── auth_service.py
│   │   │       ├── diagnostic_service.py
│   │   │       ├── roadmap_service.py
│   │   │       ├── recommendation_service.py
│   │   │       ├── analytics_service.py
│   │   │       ├── dashboard_service.py
│   │   │       ├── mentor_service.py
│   │   │       ├── tenant_service.py
│   │   │       ├── user_service.py
│   │   │       ├── topic_service.py
│   │   │       ├── goal_service.py
│   │   │       ├── profile_service.py
│   │   │       ├── notification_service.py
│   │   │       ├── community_service.py
│   │   │       ├── digital_twin_service.py
│   │   │       ├── ml_platform_service.py
│   │   │       ├── ai_request_service.py
│   │   │       ├── ai_execution_service.py
│   │   │       ├── outbox_service.py
│   │   │       └── many other feature services
│   │   ├── core/                              # Shared config/security/runtime helpers
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── security.py
│   │   │   ├── security_middleware.py
│   │   │   ├── authorization.py
│   │   │   ├── metrics.py
│   │   │   ├── logging.py
│   │   │   ├── pagination.py
│   │   │   └── feature_flags.py
│   │   ├── domain/
│   │   │   ├── engines/                       # Core intelligence/learning engines
│   │   │   │   ├── adaptive_testing_engine.py
│   │   │   │   ├── recommendation_engine.py
│   │   │   │   ├── prerequisite_tracer.py
│   │   │   │   ├── weakness_modeling_engine.py
│   │   │   │   ├── knowledge_graph.py
│   │   │   │   ├── learning_profile_engine.py
│   │   │   │   ├── ml_recommendation_engine.py
│   │   │   │   └── predictive_intelligence_engine.py
│   │   │   ├── models/                        # SQLAlchemy models
│   │   │   │   ├── user.py
│   │   │   │   ├── tenant.py
│   │   │   │   ├── goal.py
│   │   │   │   ├── topic.py
│   │   │   │   ├── question.py
│   │   │   │   ├── diagnostic_test.py
│   │   │   │   ├── user_answer.py
│   │   │   │   ├── roadmap.py
│   │   │   │   ├── roadmap_step.py
│   │   │   │   ├── topic_prerequisite.py
│   │   │   │   ├── learning_profile.py
│   │   │   │   ├── notification.py
│   │   │   │   ├── feature_flag.py
│   │   │   │   ├── audit_log.py
│   │   │   │   ├── outbox_event.py
│   │   │   │   └── many additional models
│   │   │   └── services/
│   │   │       ├── auth_rules.py
│   │   │       ├── diagnostic_rules.py
│   │   │       └── roadmap_rules.py
│   │   ├── events/
│   │   │   ├── event_envelope.py
│   │   │   ├── kafka_topics.py
│   │   │   └── schema_registry.py
│   │   ├── infrastructure/
│   │   │   ├── database.py
│   │   │   ├── tenant_rls.py
│   │   │   ├── celery_app.py
│   │   │   ├── cache/
│   │   │   │   ├── cache_service.py
│   │   │   │   └── redis_client.py
│   │   │   ├── clients/
│   │   │   │   ├── ai_service_client.py
│   │   │   │   └── search_client.py
│   │   │   ├── jobs/
│   │   │   │   ├── dispatcher.py
│   │   │   │   ├── queue_config.py
│   │   │   │   └── tasks.py
│   │   │   ├── monitoring/
│   │   │   │   └── metrics_service.py
│   │   │   ├── repositories/                 # Data access layer
│   │   │   │   ├── user_repository.py
│   │   │   │   ├── tenant_repository.py
│   │   │   │   ├── diagnostic_repository.py
│   │   │   │   ├── roadmap_repository.py
│   │   │   │   ├── topic_repository.py
│   │   │   │   ├── goal_repository.py
│   │   │   │   ├── outbox_repository.py
│   │   │   │   └── many other repositories
│   │   │   └── streaming/
│   │   │       └── kafka_client.py
│   │   ├── presentation/                      # API routes
│   │   │   ├── api_router.py
│   │   │   ├── auth_routes.py
│   │   │   ├── diagnostic_routes.py
│   │   │   ├── roadmap_routes.py
│   │   │   ├── dashboard_routes.py
│   │   │   ├── analytics_routes.py
│   │   │   ├── tenant_routes.py
│   │   │   ├── user_routes.py
│   │   │   ├── topic_routes.py
│   │   │   ├── goal_routes.py
│   │   │   ├── mentor_routes.py
│   │   │   ├── ml_routes.py
│   │   │   ├── ai_routes.py
│   │   │   ├── community_routes.py
│   │   │   ├── notification_routes.py
│   │   │   ├── search_routes.py
│   │   │   ├── realtime_routes.py
│   │   │   ├── file_routes.py
│   │   │   ├── feature_flag_routes.py
│   │   │   ├── outbox_routes.py
│   │   │   ├── audit_routes.py
│   │   │   └── middleware/
│   │   │       ├── logging_middleware.py
│   │   │       └── rate_limiter.py
│   │   ├── realtime/
│   │   │   ├── distributed_bus.py
│   │   │   └── hub.py
│   │   └── schemas/                           # Pydantic API schemas
│   │       ├── auth_schema.py
│   │       ├── diagnostic_schema.py
│   │       ├── roadmap_schema.py
│   │       ├── user_schema.py
│   │       ├── topic_schema.py
│   │       ├── goal_schema.py
│   │       ├── analytics_schema.py
│   │       ├── dashboard_schema.py
│   │       ├── mentor_schema.py
│   │       ├── notification_schema.py
│   │       └── many additional schemas
│   ├── scripts/
│   │   ├── chaos/
│   │   ├── load/
│   │   └── ops/
│   ├── sql/
│   │   ├── postgres_tenant_rls.sql
│   │   └── postgres_tenant_rls_phase2.sql
│   └── tests/                                 # Backend pytest suite
│
├── learning-platform-frontend/                # Main Next.js frontend
│   ├── package.json
│   ├── package-lock.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── playwright.config.ts
│   ├── vitest.config.mts
│   ├── middleware.ts
│   ├── proxy.ts
│   ├── Dockerfile
│   ├── Dockerfile.e2e
│   ├── app/                                   # App Router pages
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── auth/
│   │   ├── login/
│   │   ├── register/
│   │   ├── community/
│   │   ├── dashboard/
│   │   ├── diagnostic/
│   │   ├── goals/
│   │   ├── mentor/
│   │   ├── progress/
│   │   ├── roadmap/
│   │   ├── topic/
│   │   ├── (admin)/
│   │   ├── (auth)/
│   │   ├── (independent-learner)/
│   │   ├── (mentor)/
│   │   ├── (student)/
│   │   ├── (super-admin)/
│   │   └── (teacher)/
│   ├── components/
│   │   ├── auth/
│   │   ├── admin/
│   │   ├── brand/
│   │   ├── charts/
│   │   ├── chat/
│   │   ├── community/
│   │   ├── dashboard/
│   │   ├── diagnostic/
│   │   ├── independent-learner/
│   │   ├── landing/
│   │   ├── landing-new/
│   │   ├── layout/
│   │   ├── layouts/
│   │   ├── marketing/
│   │   ├── mentor/
│   │   ├── ops/
│   │   ├── progress/
│   │   ├── providers/
│   │   ├── routing/
│   │   ├── student/
│   │   ├── super-admin/
│   │   ├── teacher/
│   │   └── ui/
│   ├── features/
│   │   ├── auth/
│   │   ├── community-admin/
│   │   ├── diagnostic/
│   │   └── roadmap/
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useDashboard.ts
│   │   ├── useTenant.ts
│   │   ├── useTenantScope.ts
│   │   ├── useAdaptiveStudentUI.ts
│   │   └── useDiagnosticCountdown.ts
│   ├── lib/
│   │   └── api.ts
│   ├── public/
│   │   ├── assets/
│   │   └── premium/
│   ├── services/
│   │   ├── apiClient.ts
│   │   ├── authService.ts
│   │   ├── diagnosticService.ts
│   │   ├── roadmapService.ts
│   │   ├── analyticsService.ts
│   │   ├── dashboardService.ts
│   │   ├── mentorService.ts
│   │   ├── mlService.ts
│   │   ├── tenantService.ts
│   │   └── many other frontend services
│   ├── store/
│   ├── stores/
│   │   └── useDiagnosticTestStore.ts
│   ├── tests/
│   │   └── e2e/
│   │       ├── learner-journey.spec.ts
│   │       ├── live-login.spec.ts
│   │       ├── live-onboarding.spec.ts
│   │       └── tenant-switching.spec.ts
│   ├── types/
│   │   ├── auth.ts
│   │   ├── diagnostic.ts
│   │   ├── roadmap.ts
│   │   ├── analytics.ts
│   │   ├── dashboard.ts
│   │   ├── tenant.ts
│   │   ├── topic.ts
│   │   └── many additional type definitions
│   └── utils/
│       ├── appRoutes.ts
│       ├── authToken.ts
│       ├── cn.ts
│       ├── roleRedirect.ts
│       └── tenantLabels.ts
│
├── ai_service/                                # Separate AI microservice scaffold
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── service.py
│   ├── llm_client.py
│   ├── prompts.py
│   ├── schemas.py
│   ├── config.py
│   ├── cache.py
│   └── guardrails.py
│
├── docs/                                      # Architecture and planning docs
│   ├── learning_intelligence_platform_architecture.md
│   ├── production-deployment.md
│   ├── launch_checklist.md
│   ├── reliability_runbook.md
│   ├── backend_scalability_architecture.md
│   ├── distributed_system_architecture.md
│   ├── multi_agent_ai_architecture.md
│   ├── autonomous_learning_agent.md
│   ├── digital_twin_architecture.md
│   ├── ml_platform_architecture.md
│   ├── demo_seed_data.md
│   └── other supporting docs
│
├── k8s/                                       # Kubernetes manifests
│   ├── namespace.yaml
│   ├── api.yaml
│   ├── frontend.yaml
│   ├── ai-service.yaml
│   ├── workers.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── network-policy.yaml
│   ├── cronjobs.yaml
│   └── secrets.example.yaml
│
├── monitoring/                                # Observability stack
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts.yml
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── provisioning/
│   └── alertmanager/
│       └── alertmanager.yml
│
├── nginx/
│   ├── nginx.conf
│   ├── frontend_gateway.conf
│   └── conf.d/
│       └── default.conf
│
├── Premiumsaaslandingpage-main/               # Separate landing page assets/reference
└── logs/                                      # Runtime logs
```

### Generated Or Environment Folders

These folders exist in the workspace but are not part of the main hand-written source code:

```text
.git/
.venv/
.venv-1/
venv/
.pytest_cache/
__pycache__/
backend/__pycache__/
backend/.pytest_cache/
learning-platform-frontend/.next/
learning-platform-frontend/node_modules/
learning-platform-frontend/test-results/
learning_intelligence_platform.egg-info/
```

### Clear Overview Of The Structure

- `backend/` contains the complete API, business logic, engines, models, repositories, jobs, and tests.
- `learning-platform-frontend/` contains the Next.js app, role-based interfaces, reusable components, frontend services, and e2e tests.
- `ai_service/` is a separate AI-focused service for prompt handling, guardrails, schemas, and LLM integration.
- `docs/`, `k8s/`, `monitoring/`, and `nginx/` contain deployment, architecture, observability, and gateway configuration.
- Root-level files like `README.md`, `blueprint.md`, and this overview file explain the platform and document progress.

## b) Key Modules Explanation

### Authentication Module

The authentication module manages login, token generation, token validation, and protected user access. It uses JWT-based security and works with role and tenant context to make sure each user only accesses allowed data.

### Diagnostic Engine

The diagnostic engine controls the learner test flow, including starting a test, answering questions, moving to the next question, and finalizing the result. It is responsible for identifying learner strengths and weak areas from submitted answers.

### Roadmap Generator

The roadmap generator takes diagnostic results and converts them into a personalized learning plan. It checks weak topics, prerequisites, and learner goals, then prepares structured roadmap steps for progress tracking.

### Database Models

The database models define the platform data structure for users, tenants, topics, questions, diagnostic tests, answers, roadmaps, and progress. These models keep the system organized and support multi-tenant learning workflows.

## c) Important Code Snippets

### Diagnostic submit flow

```python
@router.post("/submit", response_model=DiagnosticSubmitResponse)
async def submit_diagnostic(payload: DiagnosticSubmitRequest, db: AsyncSession = Depends(get_db_session), current_user=Depends(require_profile_completed)):
    result = await DiagnosticService(db).finalize_test(
        test_id=payload.test_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    _, should_enqueue = await RoadmapService(db).ensure_generation_requested(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        goal_id=result["goal_id"],
        test_id=payload.test_id,
    )
    return result
```

### Roadmap generation flow

```python
@router.post("/generate", response_model=RoadmapResponse)
async def generate_roadmap(payload: RoadmapGenerateRequest, db: AsyncSession = Depends(get_db_session), current_user=Depends(require_profile_completed)):
    roadmap_service = RoadmapService(db)
    roadmap, should_enqueue = await roadmap_service.ensure_generation_requested(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        goal_id=payload.goal_id,
        test_id=payload.test_id,
    )
    return roadmap_service.serialize_roadmap(roadmap)
```

### JWT access token creation

```python
def create_access_token(subject: str | dict[str, Any], expires_delta: timedelta | None = None, *, token_id: str | None = None) -> str:
    settings = get_settings()
    return _create_token(
        subject,
        token_type=TOKEN_TYPE_ACCESS,
        expires_delta=expires_delta or timedelta(minutes=settings.access_token_expire_minutes),
        token_id=token_id,
    )
```

### Diagnostic start flow

```python
@router.post("/start", response_model=DiagnosticStartResponse)
async def start_diagnostic(payload: DiagnosticStartRequest, db: AsyncSession = Depends(get_db_session), current_user=Depends(require_profile_completed)):
    return await DiagnosticService(db).start_test(current_user.id, payload.goal_id, current_user.tenant_id)
```

## d) Technologies Used

- FastAPI for backend API development
- PostgreSQL for relational database storage
- React with Next.js for frontend development
- TypeScript for frontend type safety
- JWT for authentication and authorization
- SQLAlchemy for ORM and async database access
- Alembic for database migrations
- Redis for caching and background processing support
- Celery for background jobs
- Playwright for end-to-end testing
- Vitest and Testing Library for frontend testing
- Pytest for backend testing
- Docker Compose for local environment setup
- Kubernetes for deployment manifests

## 3. Flow Diagram

```text
User
  ->
Diagnostic Test
  ->
Answer Evaluation
  ->
Analysis
  ->
Weak Areas Identified
  ->
Roadmap Generation
  ->
Personalized Learning Plan
```

## Simple One-Line Flow

```text
User -> Diagnostic Test -> Analysis -> Weak Areas -> Roadmap
```
