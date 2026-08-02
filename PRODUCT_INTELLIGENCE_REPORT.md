# Product Intelligence Report

Project: Universal Learning Intelligence Platform / Learning Intelligence Platform  
Repository inspected: `/home/charan_derangula/projects/intelligentSystems`  
Inspection date: 2026-08-02  
Scope note: Metrics exclude dependency/build/runtime artifacts such as `.git`, `.venv`, `venv`, `node_modules`, `.next`, `dist`, `__pycache__`, `.pytest_cache`, and test output directories.

## 1. Executive Understanding

### What Is This Product?

This is a multi-tenant SaaS learning intelligence platform. It combines diagnostics, topic graphs, personalized roadmaps, learner progress tracking, role-based dashboards, mentor workflows, analytics, community features, gamification, AI-assisted mentoring/content generation, and early ML/digital-twin capabilities.

The project is split into:

- `backend/`: FastAPI modular monolith with layered architecture.
- `learning-platform-frontend/`: Next.js app-router frontend.
- `ai_service/`: separate FastAPI AI orchestration service.
- `k8s/`, `docker-compose.yml`, `nginx/`, `monitoring/`: deployment, gateway, and observability assets.
- `docs/`: architecture, reliability, business, ML, AI, RLS, and launch documents.
- `Premiumsaaslandingpage-main/`: separate premium landing page package wired into Docker Compose through an Nginx frontend gateway.

### Problem It Solves

The platform addresses static learning paths by converting diagnostic performance and learning activity into adaptive, role-aware guidance:

```text
Diagnostic Test -> Topic Scores -> Weak Topics -> Prerequisites -> Personalized Roadmap
```

For organizations, it adds tenant-level management, teacher/admin dashboards, analytics, content/goals/topics management, and operational controls.

### Users

- Students.
- Independent learners.
- Teachers.
- Mentors.
- Institution admins.
- Super admins / platform operators.

### Customers

From `docs/business_strategy.md`, target customers are:

- Individual learners.
- Cohort operators and bootcamps.
- Schools, universities, and enterprise learning teams.

### Why It Was Built

The repository documentation positions the product as an AI-native learning and career platform that turns assessment/progress signals into personalized roadmaps, mentor guidance, analytics, and job-readiness support.

### Core Innovation

Implemented or scaffolded innovation areas:

- Adaptive diagnostic engine.
- Topic prerequisite graph and graph indexing.
- Weakness modeling.
- Personalized roadmap generation.
- Rule-based recommendation engine with ML rollout path.
- Multi-agent AI mentor orchestration.
- Learner digital twin computed from existing learning signals.
- Tenant-aware SaaS architecture with RLS rollout scripts.

### Current Maturity Level

Beyond prototype. The backend is substantial and production-oriented, with many tests, migrations, role-based APIs, outbox reliability, Docker/Kubernetes assets, and monitoring. The frontend has broad route coverage but test failures and likely incomplete parity with backend capabilities. AI/ML features are partially implemented and partly architectural/scaffolded.

### Current Completion Level

Estimated overall completion: 68%.

Evidence:

- Backend domain/API surface is broad and largely implemented.
- Frontend has 56 app pages and role panels.
- Deployment and observability assets exist.
- Tests exist but current full backend and frontend test runs are not clean.
- ML pipeline has registry/feature/training APIs but no found serialized model artifacts or offline training scripts.
- Enterprise-grade features like SSO, centralized audit logging, fully proven RLS coverage, billing enforcement, and disaster recovery automation are incomplete.

### Estimated Development Effort

Estimated effort represented: 10-18 engineer-months for the owned code and documentation present, assuming experienced full-stack/backend-heavy development. Additional production hardening likely needs 3-6 engineer-months.

## 2. Project Metrics

| Metric | Count |
|---|---:|
| Owned code/docs/config lines | 108,118 |
| Files in repo including dependencies/build outputs | 25,684 |
| Backend Python files | 491 |
| Backend route files | 30 |
| Backend API endpoints detected | 187 |
| Backend application services | 68 |
| Backend repositories | 35 |
| Backend domain models | 74 |
| Backend domain engines | 18 |
| Backend schema files | 28 |
| Alembic migrations | 69 |
| Backend test files | 101 |
| Frontend TSX files | 154 |
| Frontend TS files | 86 |
| Frontend app pages | 56 |
| Frontend layouts/layout components | 11 |
| Frontend components | 82 |
| Frontend hooks | 8 |
| Frontend services | 28 |
| AI service Python files | 8 |
| Docs markdown files in `docs/` | 15 |
| Kubernetes manifests | 12 |
| Test files total detected | 113 |
| Docker Compose services | 15 |

## 3. Product Inventory By Module

| Module | Purpose | Features | Current Implementation | Dependencies | Missing Functionality | Completion |
|---|---|---|---|---|---|---:|
| Auth & Identity | Secure user access | Register, login, refresh, logout, sessions, invite accept, email verification, password reset, MFA, JWT cookies/headers | FastAPI routes, bcrypt, JWT, refresh/session tables, token blacklist, auth logs | `python-jose`, `bcrypt`, DB, cookies | SSO/OIDC/SAML not found; production email provider depends on config | 80% |
| Tenancy | Multi-tenant SaaS boundaries | Tenant records, memberships, roles, personal tenant type, RLS context | Tenant models, membership model, repository filters, middleware, RLS scripts | PostgreSQL, SQLAlchemy | Full DB-proven RLS coverage not verified cleanly; tests currently failing | 72% |
| User/Profile | Learner/person profile | Profile status, progress, onboarding events, photo upload | Profile APIs/services/files | DB, S3-compatible config optional | Rich profile UX parity not fully proven | 70% |
| Diagnostics | Assess knowledge | Start test, answer, submit, complete, result, performance, gaps, next question, timer/state persistence | Diagnostic services split into selection/scoring/analysis/completion/expiry | Questions/topics, DB | Production content coverage depends on seed/import | 82% |
| Topics & Questions | Curriculum graph | Topics CRUD, graph, prerequisites, question CRUD/import/export, AI explain/generate | Topic routes/service/repository, question serializer, graph engines | DB, optional AI service | Authoring UX completeness uncertain | 78% |
| Goals | Learning goals | Goals CRUD, goal-topic links, user goal selection/current goal | Goal/user-goal routes/services/repositories | DB | Some tests failing around fake contract drift | 75% |
| Roadmaps | Personalized learning plans | Generate roadmap, view/list, update step, adaptive refresh, cache | Roadmap service/repository, recommendation engines, cache integration | DB, Redis optional, diagnostics | Cache interface test failure; frontend limited to main learner paths | 78% |
| Dashboards | Role-specific summaries | Student, independent learner, admin, teacher, experiments, community | Backend dashboard routes, frontend pages | Analytics/services | Frontend tests fail without AuthProvider wrapper | 68% |
| Analytics | Progress and operational insights | Overview, mastery, trends, retention, weak topics, skill vectors, snapshots, failed job retry | Analytics routes/services/snapshots/materialized-view migration | DB, Celery, outbox | Freshness and cohort depth listed as gaps in docs | 72% |
| Mentor | Human/AI mentorship | Learners, chat, fallback, async status, ack, suggestions, progress analysis, notifications, agent status/run, hybrid network | Mentor backend + frontend pages/services + AI service | AI service optional, DB | Full mentor workflow depth uncertain | 70% |
| AI Service | LLM orchestration | Roadmap generation, mentor chat, progress analysis, topic explanation, question generation, multi-agent routing | Separate FastAPI service, OpenAI-compatible client, Groq/OpenAI/fallback providers, TTL cache, guardrails | `openai`, provider API keys | No vector retrieval or persistent memory store in AI service; no LLM eval harness found | 65% |
| ML Platform | Predictions/feature pipeline | Feature snapshots, train metadata, recommendation/difficulty/dropout inference APIs | ML routes/service/models/docs | DB | No actual model artifact training scripts found; production ML is not default | 45% |
| Digital Twin | Learner state simulation | Current model, simulations, decision support | Backend service/route/schema, student frontend page | Learning events, topic scores, ML features | Separate persisted twin state machine not found by design | 60% |
| Community | Social learning | Communities, members, threads, replies, resolve, badges | Routes/services/models/frontend page | DB | Moderation depth/abuse controls partial | 68% |
| Social Network | Learner graph | Network, follow, unfollow | Social routes/service/model/frontend service | DB | Rich social UX not found | 55% |
| Gamification | Motivation | Profile, leaderboard, activity, events, badges | Routes/service/models | DB | Economy/rules depth uncertain | 60% |
| Career | Job readiness | Overview, readiness, resume, interview prep, role bootstrap | Career routes/services/engines/frontend page | DB, AI optional | Employer integrations not found | 62% |
| Ecosystem/Marketplace | Platform extensions | Marketplace, reviews, plugins, API clients, plans, subscription | Routes/models/services/admin frontend page | DB | Payment/billing enforcement not found | 50% |
| Files | Upload assets | Upload request, finalize, retrieve | File routes/service, S3 config | S3-compatible storage optional | Antivirus/content scanning not found | 58% |
| Search | Content search | `/search`, DB/search-client abstraction | Search service/client | DB, optional external search | External search deployment not found | 55% |
| Notifications | Learner/admin notifications | List, mark read, generate | Notification routes/services/repositories/frontend | DB, jobs | Push/mobile channels not found | 60% |
| Ops | Operational controls | Feature flags, outbox, audit export/names | Ops routes, repositories, tests | DB, filesystem audit logs | Centralized audit storage not found | 67% |
| Realtime | Websocket events | `/realtime/ws`, distributed Redis pubsub | Realtime hub/bus/routes | Redis | Auth status for websocket not evident in decorator extraction | 55% |
| DevOps/Observability | Run/deploy/observe | Compose, Kubernetes, Nginx, Prometheus, Grafana, Alertmanager, Sentry optional, scripts | Full stack assets present | Docker, K8s, Redis, Postgres | Managed-cloud implementation and backup automation are scripts/docs, not verified | 75% |

## 4. Feature Catalogue

| Feature | User Value | Technical Implementation | BE | FE | DB | API | AI | Status |
|---|---|---|---|---|---|---|---|---|
| Registration | Account creation | `auth_routes.py`, `AuthService.register` | Yes | Yes | users/tenants/sessions | Yes | No | Implemented |
| Login/session refresh | Persistent access | JWT, refresh sessions, cookies | Yes | Yes | sessions/token tables | Yes | No | Implemented |
| Logout/logout all | Session control | session revocation + blacklist | Yes | Yes | sessions/token_blacklist | Yes | No | Implemented |
| Invite accept | Tenant onboarding | invite JWT and auth service | Yes | Yes | users/memberships | Yes | No | Implemented |
| Email verification | Trust/account integrity | token generation/confirm routes | Yes | Yes | auth_tokens/users | Yes | No | Partial |
| Password reset | Account recovery | reset token routes | Yes | Yes | auth_tokens | Yes | No | Partial |
| MFA setup/enable/disable | Strong auth | TOTP helpers/routes | Yes | Yes | user profile/auth | Yes | No | Partial |
| Role-based dashboards | Role-specific home | dashboard routes and role layouts | Yes | Yes | analytics/user data | Yes | No | Partial |
| Tenant admin panel | Manage org | admin pages/users/content/goals/ml/ecosystem | Yes | Yes | many | Yes | Partial | Partial |
| Super-admin panel | Platform ops | tenants/outbox/health/dashboard pages | Yes | Yes | tenants/outbox | Yes | No | Partial |
| Teacher panel | Cohort insight | teacher dashboard/insights/students pages | Yes | Yes | analytics | Yes | No | Partial |
| Student dashboard | Learner workspace | student dashboard page + service | Yes | Yes | analytics/roadmap | Yes | No | Implemented, tests failing |
| Independent learner workspace | Self-serve personal tenant | independent learner pages/layout | Yes | Yes | personal tenant type | Yes | No | Partial |
| Goal selection | Personalized target | user goal routes/services | Yes | Yes | user_goals/goals | Yes | No | Implemented |
| Goal CRUD | Admin content management | goal routes/services/repo | Yes | Yes | goals/goal_topics | Yes | No | Partial |
| Topic CRUD | Curriculum management | topic routes/services/repo | Yes | Yes | topics | Yes | No | Implemented |
| Prerequisite graph | Learning dependency reasoning | topic_prerequisites + engines | Yes | Yes | topic_prerequisites | Yes | No | Implemented |
| Question bank | Assessment content | question routes/import/export | Yes | Yes | questions/options | Yes | AI generate | Implemented |
| CSV question import/export | Admin bulk operations | import/export endpoints | Yes | Yes | questions | Yes | No | Implemented |
| Diagnostic start | Begin assessment | diagnostic lifecycle service | Yes | Yes | diagnostic_tests | Yes | No | Implemented |
| Diagnostic answer/submit | Capture performance | scoring and answer persistence | Yes | Yes | user_answers/topic_scores | Yes | No | Implemented |
| Adaptive next question | Better assessment | adaptive testing engine | Yes | Yes | questions/state | Yes | No | Implemented |
| Diagnostic result | Learner feedback | analysis service/result schema | Yes | Yes | diagnostic/topic scores | Yes | No | Implemented |
| Timer/state enforcement | Test integrity | diagnostic test state model/migrations | Yes | Yes | diagnostic_test_states | Yes | No | Implemented |
| Roadmap generation | Personalized plan | roadmap service + recommendation | Yes | Yes | roadmaps/steps | Yes | Optional | Implemented |
| Roadmap progress | Track execution | patch step route | Yes | Yes | roadmap_steps | Yes | No | Implemented |
| Adaptive roadmap refresh | Update plan | `adaptive-refresh` route | Yes | Service | roadmaps | Yes | Optional | Partial |
| Recommendation engine | Prioritize topics | rule/ML engines | Yes | Panel support | topic_scores | Yes | No | Implemented |
| Retention/revision | Remember material | retention service/revision route | Yes | Some | topic reviews/scores | Yes | No | Partial |
| Learning profile | Personalize pace/style | profile engine/service | Yes | Yes | learning_profiles | Yes | No | Partial |
| Skill vectors | Learner skill model | vector service/model | Yes | Analytics | user_skill_vectors | Yes | No | Implemented |
| Analytics overview | Observe progress | analytics service/routes | Yes | Yes | snapshots/events | Yes | No | Implemented |
| Precomputed analytics | Faster dashboards | snapshot service/jobs | Yes | Admin | analytics_snapshots | Yes | No | Partial |
| Failed analytics jobs retry | Operability | dead letter APIs | Yes | Ops | dead_letter_events | Yes | No | Implemented |
| Mentor chat | Guidance | backend chat routes + AI service | Yes | Yes | mentor messages/requests | Yes | Yes | Implemented |
| Async AI request status | Nonblocking AI | ai_requests/outbox/jobs | Yes | Yes | ai_requests | Yes | Yes | Implemented |
| Multi-agent AI mentor | Specialized guidance | AI service routes agents | Yes | Metadata support | Not separately persisted | Yes | Yes | Partial |
| Topic explanation AI | Explain topics | AI service + topic route | Yes | Admin/topic support | ai_requests | Yes | Yes | Partial |
| AI question generation | Content creation | AI service + topic route | Yes | Admin/topic support | questions | Yes | Yes | Partial |
| Digital twin | Simulate learner future | service/route/student page | Yes | Yes | derived from existing tables | Yes | Optional | Partial |
| ML feature snapshot | ML foundation | `ml_feature_snapshots` | Yes | Admin ML page | Yes | Yes | No | Partial |
| ML train metadata | Version experiments | `ml_training_runs`, `ml_model_registry` | Yes | Admin ML page | Yes | Yes | No | Prototype |
| ML inference | Predictions | recommendations/difficulty/dropout routes | Yes | Partial | model registry/features | Yes | No | Prototype |
| Community | Peer learning | communities/members/threads/replies | Yes | Yes | community tables | Yes | No | Implemented |
| Badges/leaderboard | Motivation | gamification routes/service | Yes | Some | badges/events/profile | Yes | No | Partial |
| Social following | Network effects | social routes/service | Yes | Student network | social_follows | Yes | No | Partial |
| Career readiness | Job outcomes | career engine/routes/page | Yes | Yes | job roles/skills | Yes | Optional | Partial |
| Marketplace | Ecosystem | listings/reviews/plugins/API clients | Yes | Admin ecosystem | marketplace/plugin tables | Yes | No | Prototype |
| Subscription plans | Monetization | subscription plan model/routes | Yes | Admin ecosystem | subscription tables | Yes | No | Prototype |
| File upload | Content/profile assets | upload/finalize/get file APIs | Yes | Service | file_assets | Yes | No | Partial |
| Search | Discovery | search route/service/client | Yes | Service | DB/external optional | Yes | No | Partial |
| Notifications | Re-engagement | notification route/service/panel | Yes | Yes | notifications | Yes | No | Partial |
| Feature flags | Controlled rollout | ops routes, feature service | Yes | Admin | feature_flags | Yes | No | Implemented, tests failing |
| Audit logs | Compliance visibility | audit route/service/log file | Yes | Ops | file/audit model | Yes | No | Partial |
| Outbox reliability | Async durability | outbox models/jobs/ops routes | Yes | Super-admin ops | outbox/dead letter | Yes | No | Implemented |
| Realtime websocket | Live updates | hub/distributed bus/ws route | Yes | Provider | Redis pubsub | WS | No | Partial |
| Monitoring metrics | Operability | `/metrics`, Prometheus/Grafana | Yes | No | N/A | Yes | No | Implemented |
| Kubernetes deployment | Production deployment path | manifests for API/frontend/AI/workers | N/A | N/A | N/A | N/A | N/A | Partial |
| Billing/payment processing | Monetization execution | Not found. | No | No | subscription tables only | No | No | Planned |
| SSO/SAML/OIDC | Enterprise auth | Not found. | No | No | No | No | No | Planned |
| Centralized logs/audit store | Enterprise compliance | Not found; docs note audit is file-based | Partial | No | audit table exists | Partial | No | Planned |

## 5. User Flows

### Registration

Screens/services:

- `app/register/page.tsx`
- `app/auth/page.tsx`
- `components/auth/AuthPageClient.tsx`
- `services/authService.ts`
- Backend `/auth/register`

Flow:

1. User submits account details.
2. Frontend calls `/auth/register`.
3. Backend validates password, creates tenant/personal tenant as needed, creates user/session, can emit verification email.
4. User proceeds to profile/onboarding/role redirect.

### Login

Screens/services:

- `app/login/page.tsx`
- `app/auth/page.tsx`
- `services/authService.ts`
- `components/providers/AuthProvider.tsx`

Flow:

1. User submits credentials.
2. Frontend calls `/auth/login`.
3. Backend returns tokens/cookies and session metadata.
4. Role redirect uses `utils/roleRedirect.ts`.

### Dashboard

Screens:

- Student: `app/(student)/student/dashboard/page.tsx`
- Independent learner: `app/(independent-learner)/independent-learner/dashboard/page.tsx`
- Teacher: `app/(teacher)/teacher/dashboard/page.tsx`
- Admin: `app/(admin)/admin/dashboard/page.tsx`
- Super admin: `app/(super-admin)/super-admin/dashboard/page.tsx`
- Mentor: `app/(mentor)/mentor/dashboard/page.tsx`

Backend:

- `/dashboard/student`
- `/dashboard/independent-learner`
- `/dashboard/admin`
- `/dashboard/teacher`
- `/dashboard/experiments`
- `/dashboard/community`

### Learning/Diagnostic

Screens:

- `app/diagnostic/page.tsx`
- `app/(student)/student/diagnostic/page.tsx`
- `app/(student)/student/diagnostic/result/page.tsx`
- independent learner diagnostic/result equivalents.
- Diagnostic components: intro, goal selection, test screen, timer, question card, warning modal, result dashboard.

Flow:

1. Select/current goal.
2. Start diagnostic.
3. Answer questions with timer/state.
4. Submit/complete.
5. View result.
6. Generate roadmap.

### Roadmap

Screens:

- `app/roadmap/page.tsx`
- `app/(student)/student/roadmap/page.tsx`
- `app/(independent-learner)/independent-learner/roadmap/page.tsx`
- topic detail pages under student and independent learner paths.

Backend:

- `/roadmap/generate`
- `/roadmap/view`
- `/roadmap`
- `/roadmap/{user_id}`
- `/roadmap/steps/{step_id}`
- `/roadmap/adaptive-refresh`

### AI Chat / Mentor

Screens:

- `app/(student)/student/mentor/page.tsx`
- `app/(independent-learner)/independent-learner/mentor/page.tsx`
- `app/(mentor)/mentor/chat/page.tsx`
- mentor dashboard/network pages.

Backend:

- `/mentor/chat`
- `/mentor/chat/fallback`
- `/mentor/chat/status/{request_id}`
- `/mentor/suggestions`
- `/mentor/progress-analysis`
- `/mentor/agent/run`
- `/ai/chat`

AI service:

- `/mentor-response`
- `/ai/mentor-chat`
- `/ai/analyze-progress`

### Admin

Screens:

- `/admin/dashboard`
- `/admin/users`
- `/admin/content`
- `/admin/community`
- `/admin/goals`
- `/admin/feature-flags`
- `/admin/ml`
- `/admin/ecosystem`

Capabilities:

- user management, content/topics/questions, goals, feature flags, ML controls, ecosystem/marketplace controls, analytics.

### Teacher

Screens:

- `/teacher/dashboard`
- `/teacher/insights`
- `/teacher/students`

Capabilities:

- cohort/tenant analytics, weak topics, student progress. Cohort-level depth is marked as a remaining gap in docs.

### Mentor

Screens:

- `/mentor/dashboard`
- `/mentor/chat`
- `/mentor/network`

Capabilities:

- learner list, chat, suggestions, progress analysis, notifications, hybrid network/session plan.

### Analytics

Screens:

- Admin/teacher/student dashboards, progress pages, analytics components.

Backend endpoints:

- `/analytics/overview`
- `/analytics/roadmap-progress`
- `/analytics/topic-mastery`
- `/analytics/platform-overview`
- `/analytics/retention`
- `/analytics/student-insights`
- `/analytics/skill-vectors`
- `/analytics/weak-topics`
- `/analytics/learning-trends`
- `/analytics/student/{user_id}`
- `/analytics/topic/{topic_id}`
- `/analytics/precomputed/*`
- `/analytics/jobs/failed*`

### Marketplace/Ecosystem

Screens:

- `app/(admin)/admin/ecosystem/page.tsx`

Backend:

- marketplace, plugins, API clients, subscription plans, tenant subscription routes.

Payment execution: Not found.

### Communities

Screen:

- `app/community/page.tsx`
- `app/(admin)/admin/community/page.tsx`

Backend:

- communities, members, threads, replies, badges.

### Notifications

Screens/components:

- `app/(student)/student/notifications/page.tsx`
- `components/NotificationPanel.tsx`
- `components/MentorNotifications.tsx`

Backend:

- list, mark read, generate.

### Settings

Dedicated settings page: Not found.

## 6. Frontend Analysis

### Stack

- Next.js 15.2.2.
- React 19.
- TypeScript.
- React Query.
- Zustand.
- Axios.
- Tailwind CSS.
- Recharts.
- React Flow.
- Framer Motion.
- Lucide icons.
- Vitest and Playwright.

### Pages

Total app pages detected: 56.

Role groups:

- Admin: 9 pages.
- Independent learner: 11 pages.
- Mentor: 4 pages.
- Student: 13 pages.
- Super admin: 5 pages.
- Teacher: 4 pages.
- Shared/public: auth, login, register, community, dashboard, diagnostic, roadmap, landing root.

### Components

Total components under `components/`: 82.

Major component groups:

- `auth`: auth guards and auth page client.
- `providers`: auth, tenant, realtime, theme, toast.
- `layouts` and `layout`: workspace/role shells, navigation, headers.
- `diagnostic`: test, timer, result, roadmap viewer.
- `student`: roadmap/progress/adaptive guidance/demo components.
- `independent-learner`: dashboard, onboarding, welcome.
- `landing-new` and `landing`: marketing/landing experience.
- `ui`: buttons, inputs, cards, modal, skeletons, status pills, empty/error/loading states.
- `charts`: mastery/progress/distribution charts.

### Hooks

Detected hooks: 8.

Includes auth, dashboard, tenant, and feature-level hooks such as community admin.

### Contexts/Providers

- `AuthProvider`
- `TenantProvider`
- `RealtimeProvider`
- `ThemeProvider`
- `ToastProvider`
- root `app/providers.tsx`

### Routing And Protected Routes

- App Router route groups by role.
- Middleware file exists: `learning-platform-frontend/middleware.ts`.
- Auth guards: `RequireAuth`, `RequireRole`, `AccessState`.
- Role redirect utility: `utils/roleRedirect.ts`.

### State Management

- React context providers for auth/tenant/theme/realtime/toast.
- React Query dependency is present.
- Zustand store: `stores/useDiagnosticTestStore.ts`.

### API Integrations

Frontend service files map directly to backend resources:

- `authService.ts`: auth and current user.
- `analyticsService.ts`: analytics endpoints.
- `dashboardService.ts`: dashboard endpoints.
- `diagnosticService.ts`: diagnostic endpoints.
- `roadmapService.ts`: roadmap endpoints.
- `topicService.ts`: topics/questions/prerequisites.
- `goalService.ts`: goals/user goals.
- `mentorService.ts`, `mentorInsightsService.ts`: mentor endpoints.
- `aiService.ts`: AI chat.
- `mlService.ts`: ML overview/features/train.
- `ecosystemService.ts`: marketplace/plugins/API clients/plans/subscription.
- `opsService.ts`: feature flags/outbox.
- `fileService.ts`: upload/finalize.
- `healthService.ts`: health endpoint.

### Frontend Gaps

- Two current unit tests fail because student pages use `useAuthContext` without an `AuthProvider` test wrapper.
- Dedicated settings page: Not found.
- Frontend parity for all backend endpoints is not complete; several APIs are service-only or admin-only.

## 7. Backend Analysis

### Stack

- Python 3.11+.
- FastAPI.
- SQLAlchemy async ORM.
- Alembic.
- PostgreSQL/asyncpg.
- Celery.
- Redis.
- Pydantic v2.
- JWT auth.
- Prometheus client.
- SlowAPI rate limiting.
- Sentry optional.

### Architecture

The backend follows:

```text
Route -> Service -> Engine -> Repository -> Database
```

Layers:

- `presentation`: FastAPI routes and middleware.
- `schemas`: Pydantic request/response contracts.
- `application/services`: use-case orchestration.
- `domain/engines`: learning/AI/ML business logic.
- `domain/models`: SQLAlchemy models.
- `infrastructure/repositories`: data access.
- `infrastructure/jobs`: Celery tasks and dispatch.
- `events` and `infrastructure/streaming`: Kafka/event abstractions.
- `realtime`: websocket hub and distributed bus.

### Services

68 application service files were detected. Major services include auth, sessions, tokens, diagnostics, roadmap, recommendation, analytics, analytics snapshots, dashboard, mentor, AI request/execution, topic, goal, profile, tenant, user, notifications, community, gamification, career, ML platform, digital twin, outbox, audit, search, file storage, Kafka producer/consumer, graph index, learning event/profile, feature store, and retention.

### Repositories

35 repository files were detected. These cover users, tenants, roles, auth/session/token tables, diagnostics, topics/scores, goals, roadmaps, resources, analytics snapshots, mentor messages/chats/students, gamification, community, outbox/dead letters, notifications, learning profiles, feature vectors, event consumer state, and stream offsets.

### Controllers / Routes

30 route files and 187 FastAPI route decorators were detected.

### Middleware

- Request logging.
- Rate limiting.
- CORS.
- Security headers.
- CSRF for cookie-authenticated mutating requests.
- Community-auth defensive middleware.
- Tenant-context middleware.

### Business Logic

Major domain engines:

- Adaptive testing.
- Career path planner.
- Content recommendation.
- Experiment engine.
- Job readiness.
- Knowledge graph.
- Learning profile.
- Learning simulation.
- Mentor LLM engine.
- ML recommendation.
- Predictive intelligence.
- Prerequisite tracer.
- Recommendation engine.
- Rule engine.
- Skill graph.
- Topic difficulty.
- Weakness modeling.

### Background Jobs

Celery is used for:

- Outbox processing.
- Outbox metrics refresh.
- Stuck outbox recovery.
- Cleanup.
- Analytics/rebuild jobs.
- Domain event consumers/projections.

Exact task declarations are in `backend/app/infrastructure/jobs/tasks.py`. A backend test currently fails when run from `backend/` because it tries to read `backend/app/infrastructure/jobs/tasks.py` relative to that working directory.

### Caching

- Redis client and cache service exist.
- Roadmap service uses a versioned cache key interface.
- Test failure indicates cache fake/test contract drift around `build_versioned_key`.

### Validation

- Pydantic schemas.
- Password strength validation.
- Question serialization security tests.
- Sanitization and guardrail helpers.

### AuthN/AuthZ

- JWT access and refresh tokens.
- Session table validation.
- Token blacklist.
- Role permissions map.
- Dynamic authorization policy table.
- Role dependencies and permission dependencies.
- MFA TOTP helpers.

### Events/Schedulers

- Outbox events.
- Kafka topic/schema registry/client scaffolding.
- Celery beat schedules.
- Event consumer states and processed stream events.

## 8. Database Analysis

### Database Stack

- PostgreSQL.
- SQLAlchemy models.
- Alembic migrations.
- RLS SQL scripts.

### Tables Detected From Models

`ai_requests`, `analytics_snapshots`, `api_clients`, `audit_logs`, `auth_logs`, `auth_tokens`, `authorization_policies`, `badges`, `communities`, `community_members`, `content_metadata`, `dead_letter_events`, `diagnostic_test_states`, `diagnostic_tests`, `discussion_replies`, `discussion_threads`, `event_consumer_states`, `experiment_variants`, `experiments`, `feature_flags`, `file_assets`, `gamification_events`, `gamification_profiles`, `goal_topics`, `goals`, `job_role_skills`, `job_roles`, `learning_events`, `learning_profiles`, `marketplace_listings`, `marketplace_reviews`, `mentor_chat_messages`, `mentor_memory_profiles`, `mentor_messages`, `mentor_session_memories`, `mentor_students`, `mentor_suggestions`, `ml_feature_snapshots`, `ml_model_registry`, `ml_training_runs`, `notifications`, `onboarding_events`, `outbox_events`, `plugin_registry`, `processed_stream_events`, `question_options`, `questions`, `refresh_sessions`, `refresh_tokens`, `resources`, `roadmap_steps`, `roadmaps`, `sessions`, `skills`, `social_follows`, `stream_consumer_offsets`, `subscription_plans`, `tenant_subscriptions`, `tenants`, `token_blacklist`, `topic_features`, `topic_prerequisites`, `topic_scores`, `topic_skills`, `topics`, `user_answers`, `user_features`, `user_goals`, `user_profiles`, `user_skill_vectors`, `user_tenant_roles`, `users`.

### Relations

Important relation families:

- Tenant ownership: users, goals, topics, communities, sessions, feature flags, notifications, ML features, etc.
- User to tenant memberships: `user_tenant_roles`.
- Goals to topics: `goal_topics`.
- Topic graph: `topic_prerequisites`, `topic_skills`, `topic_features`, graph index service.
- Diagnostics: `diagnostic_tests`, `diagnostic_test_states`, `user_answers`, `questions`, `question_options`.
- Roadmaps: `roadmaps`, `roadmap_steps`.
- Learning intelligence: `learning_events`, `topic_scores`, `learning_profiles`, `user_skill_vectors`.
- Mentor: `mentor_students`, `mentor_messages`, `mentor_chat_messages`, `mentor_memory_profiles`, `mentor_session_memories`, `mentor_suggestions`.
- ML: `ml_feature_snapshots`, `ml_model_registry`, `ml_training_runs`.
- Ecosystem: `marketplace_listings`, `marketplace_reviews`, `plugin_registry`, `api_clients`, `subscription_plans`, `tenant_subscriptions`.
- Reliability: `outbox_events`, `dead_letter_events`, `event_consumer_states`, `processed_stream_events`, `stream_consumer_offsets`.

### Indexes

Performance/index migrations are present:

- `20260324_0020_perf_indexes.py`
- `20260325_0027_scale_indexes.py`
- `20260402_0014_performance_indexes.py`
- `20260402_0020_analytics_snapshot_indexes.py`
- `20260430_0031_questions_sampling_index.py`
- `docs/postgres_index_recommendations.sql`
- `docs/postgres_explain_analyze_examples.sql`

### Constraints

Constraints are defined across SQLAlchemy models and migrations. Complete constraint-by-constraint extraction was not generated in this pass.

### Views / Materialized Views

Migration found: `20260328_0003_analytics_materialized_views.py`. Details exist in the migration file. Materialized analytics view support is present.

### Triggers

Not found as a separately inventoried trigger catalogue. Some migrations may contain SQL operations, but no dedicated trigger inventory was found.

### Enums

Detected enums/classes:

- `UserRole`
- `TenantType`
- `QuestionDifficulty`
- `QuestionType`
- `DiagnosticTestStatus`
- `AuthTokenPurpose`

### Migrations

69 Alembic migration files exist under `backend/alembic/versions/`, from initial schema through RLS, performance indexes, learning intelligence, ML platform, enterprise controls, auth hardening, diagnostic models, question normalization, and sampling indexes.

### Tenant Architecture

Tenant architecture is mixed:

- Application-layer tenant scoping in repositories/services.
- Middleware applies request tenant context.
- SQL session context uses `app.current_tenant_id`, `app.current_role`, `app.current_user_id`.
- PostgreSQL RLS helper functions and policies exist.
- Super-admin support exists through role and super-admin session helpers.

### RLS

RLS scripts:

- `backend/sql/postgres_tenant_rls.sql`
- `backend/sql/postgres_tenant_rls_phase2.sql`

RLS coverage is intended to cover direct tenant tables, tenant-or-global tables, and derived tenant tables. Current test run includes `test_tenant_rls_coverage.py`, but the run from `backend/` fails because the test expects `backend/sql/postgres_tenant_rls.sql` relative to repository root.

### ER Diagram

```mermaid
erDiagram
    tenants ||--o{ users : owns
    tenants ||--o{ user_tenant_roles : memberships
    users ||--o{ user_tenant_roles : has
    tenants ||--o{ goals : owns
    tenants ||--o{ topics : owns
    goals ||--o{ goal_topics : maps
    topics ||--o{ goal_topics : maps
    topics ||--o{ topic_prerequisites : topic
    topics ||--o{ topic_prerequisites : prerequisite
    topics ||--o{ questions : contains
    questions ||--o{ question_options : has
    users ||--o{ diagnostic_tests : takes
    diagnostic_tests ||--o{ user_answers : records
    diagnostic_tests ||--o{ diagnostic_test_states : state
    users ||--o{ topic_scores : earns
    topics ||--o{ topic_scores : scored
    users ||--o{ roadmaps : receives
    roadmaps ||--o{ roadmap_steps : contains
    users ||--o{ learning_events : emits
    users ||--o{ learning_profiles : has
    users ||--o{ user_skill_vectors : has
    tenants ||--o{ communities : owns
    communities ||--o{ community_members : has
    communities ||--o{ discussion_threads : contains
    discussion_threads ||--o{ discussion_replies : contains
    users ||--o{ mentor_messages : sends
    users ||--o{ mentor_chat_messages : sends
    users ||--o{ mentor_memory_profiles : has
    tenants ||--o{ feature_flags : configures
    tenants ||--o{ analytics_snapshots : aggregates
    tenants ||--o{ outbox_events : owns
    tenants ||--o{ ml_feature_snapshots : stores
    ml_model_registry ||--o{ ml_training_runs : records
```

## 9. API Analysis

### API Statistics

- Backend FastAPI route decorators detected: 187.
- AI service route decorators detected separately: 8 including aliases.
- Websocket endpoints: 1.
- Metrics endpoint: `/metrics` via `metrics_router`.
- Health endpoints: backend `/health`; AI service `/health`; root `/`.

### Endpoint Groups

Authentication:

- `POST /auth/register`
- `POST /auth/invite-accept`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/sessions`
- `POST /auth/logout-all`
- `POST /auth/email-verification/request`
- `POST /auth/email-verification/confirm`
- `POST /auth/email-verification`
- `POST /auth/verify-email`
- `POST /auth/password-reset/request`
- `POST /auth/forgot-password`
- `POST /auth/send-otp`
- `POST /auth/verify-otp`
- `POST /auth/password-reset/confirm`
- `POST /auth/reset-password`
- `POST /auth/invites`
- `POST /auth/mfa/setup`
- `POST /auth/mfa/enable`
- `POST /auth/mfa/disable`

Dashboards:

- `GET /dashboard/student`
- `GET /dashboard/independent-learner`
- `GET /dashboard/admin`
- `GET /dashboard/teacher`
- `GET /dashboard/experiments`
- `GET /dashboard/community`

Diagnostics:

- `POST /diagnostic/start`
- `POST /diagnostic`
- `POST /diagnostic/answer`
- `POST /diagnostic/submit`
- `POST /diagnostic/complete`
- `GET /diagnostic/result`
- `GET /diagnostic/{test_id}/performance`
- `GET /diagnostic/{test_id}/gaps`
- `GET /diagnostic/{test_id}`
- `GET /diagnostic/next/{test_id}`
- `POST /diagnostic/next-question`

Roadmaps:

- `POST /roadmap/generate`
- `POST /roadmap`
- `GET /roadmap/view`
- `GET /roadmap`
- `GET /roadmap/{user_id}`
- `PATCH /roadmap/steps/{step_id}`
- `POST /roadmap/adaptive-refresh`

Topics/questions:

- `GET /topics`
- `GET /topics/graph`
- `GET /topics/reasoning/{topic_id}`
- `POST /topics`
- `PUT /topics/{topic_id}`
- `DELETE /topics/{topic_id}`
- `GET /topics/questions`
- `GET /topics/prerequisites`
- `POST /topics/prerequisites`
- `DELETE /topics/prerequisites/{prerequisite_id}`
- `POST /topics/questions`
- `POST /topics/questions/import`
- `POST /topics/questions/import.csv`
- `GET /topics/questions/export`
- `GET /topics/questions/export.csv`
- `PUT /topics/questions/{question_id}`
- `DELETE /topics/questions/{question_id}`
- `GET /topics/{topic_id}`
- `POST /topics/ai/explain`
- `POST /topics/questions/ai-generate`

Goals:

- `GET /goals`
- `POST /goals`
- `GET /goals/topics`
- `POST /goals/topics`
- `DELETE /goals/topics/{link_id}`
- `PUT /goals/{goal_id}`
- `DELETE /goals/{goal_id}`
- `POST /user/goals/select`
- `GET /user/goals/current`

Users/tenants/profile:

- `POST /users`
- `POST /users/create`
- `GET /users`
- `GET /users/list`
- `GET /users/me`
- `PATCH /users/me`
- `PUT /users/complete-profile`
- `POST /tenants`
- `GET /tenants`
- `GET /profile`
- `POST /profile`
- `GET /profile/status`
- `GET /profile/progress`
- `POST /profile/upload-photo`
- `POST /profile/onboarding-events`

Analytics:

- `GET /analytics/overview`
- `GET /analytics/roadmap-progress`
- `GET /analytics/topic-mastery`
- `GET /analytics/platform-overview`
- `GET /analytics/retention`
- `GET /analytics/student-insights`
- `GET /analytics/skill-vectors`
- `GET /analytics/weak-topics`
- `GET /analytics/learning-trends`
- `GET /analytics/student/{user_id}`
- `GET /analytics/topic/{topic_id}`
- `GET /analytics/precomputed/tenant-dashboard`
- `GET /analytics/precomputed/user-learning-summary`
- `POST /analytics/precomputed/refresh`
- `GET /analytics/jobs/failed`
- `POST /analytics/jobs/failed/{dead_letter_id}/retry`

Mentor/AI:

- `GET /ai/chat`
- `POST /ai/chat`
- `GET /ai/requests/{request_id}`
- `GET /mentor/learners`
- `POST /mentor/chat`
- `POST /mentor/chat/fallback`
- `GET /mentor/chat/status/{request_id}`
- `POST /mentor/chat/ack`
- `GET /mentor/suggestions`
- `GET /mentor/progress-analysis`
- `GET /mentor/notifications`
- `GET /mentor/agent/status`
- `POST /mentor/agent/run`
- `GET /mentor/hybrid-network`
- `POST /mentor/hybrid-network/session-plan`

ML:

- `GET /ml/overview`
- `POST /ml/features/snapshot`
- `POST /ml/train`
- `GET /ml/infer/recommendations`
- `GET /ml/infer/difficulty/{topic_id}`
- `GET /ml/infer/dropout`

Community/social/gamification:

- `GET /community/communities`
- `POST /community/communities`
- `DELETE /community/communities/{community_id}`
- `GET /community/members`
- `POST /community/members`
- `GET /community/threads`
- `POST /community/threads`
- `GET /community/replies`
- `POST /community/replies`
- `PATCH /community/threads/{thread_id}/resolve`
- `GET /community/badges`
- `POST /community/badges`
- `DELETE /community/badges/{badge_id}`
- `GET /social/network`
- `POST /social/follows`
- `DELETE /social/follows/{followed_user_id}`
- `GET /gamification/me`
- `GET /gamification/leaderboard`
- `GET /gamification/activity`

Career:

- `GET /career/overview`
- `GET /career/readiness`
- `GET /career/resume`
- `POST /career/interview-prep`
- `POST /career/roles/bootstrap`

Ecosystem:

- `GET /ecosystem/overview`
- `GET /ecosystem/marketplace`
- `POST /ecosystem/marketplace`
- `POST /ecosystem/marketplace/{listing_id}/reviews`
- `GET /ecosystem/plugins`
- `POST /ecosystem/plugins`
- `GET /ecosystem/api-clients`
- `POST /ecosystem/api-clients`
- `GET /ecosystem/subscription-plans`
- `POST /ecosystem/subscription-plans`
- `POST /ecosystem/subscription`

Ops/content/files/search/realtime:

- `POST /content/metadata`
- `POST /content/index`
- `GET /content/metadata`
- `POST /files/upload-request`
- `POST /files/finalize`
- `GET /files/{asset_id}`
- `GET /search`
- `GET /notifications`
- `POST /notifications/{notification_id}/read`
- `POST /notifications/generate`
- `GET /revision/today`
- `GET /digital-twin`
- `GET /ops/feature-flags`
- `GET /ops/feature-flags/catalog`
- `POST /ops/feature-flags/{flag_name}`
- `GET /ops/outbox`
- `POST /ops/outbox/flush`
- `POST /ops/outbox/requeue-dead`
- `GET /ops/outbox/stats`
- `POST /ops/outbox/requeue-dead/{event_id}`
- `POST /ops/outbox/recover-stuck`
- `GET /ops/audit/feature-flags`
- `GET /ops/audit/feature-flags/export`
- `GET /ops/audit/feature-flags/names`
- `POST /test/generate-smart`
- `WEBSOCKET /realtime/ws`

AI service:

- `GET /health`
- `POST /predict-learning-path`
- `POST /ai/generate-roadmap`
- `POST /mentor-response`
- `POST /ai/mentor-chat`
- `POST /ai/analyze-progress`
- `POST /ai/explain-topic`
- `POST /ai/generate-questions`

### Authentication

Most backend API routes require `get_current_user`, `require_roles`, or `require_permission`. Public/credential endpoints include registration, login, refresh, invite accept, verification confirm, and password reset request/confirm variants. Websocket auth was not evident from decorator extraction.

### Inputs/Outputs

Inputs/outputs are defined via Pydantic schemas in `backend/app/schemas/` and route function signatures. Complete field-by-field schema expansion is not included here; schema files are the source of truth.

### Errors

Error handling is centralized in `presentation/error_handlers.py`, with application exceptions. Routes also raise `HTTPException` for forbidden, bad request, not found, and external AI failures.

## 10. AI Analysis

### LLMs

Providers configured in `ai_service/config.py`:

- Groq-compatible OpenAI API, default model `llama-3.3-70b-versatile`.
- OpenAI-compatible provider, default model `gpt-5-mini`.
- Fallback provider, default model `gpt-4o-mini`.

The AI service uses the OpenAI Python client `AsyncOpenAI` with the Responses API and JSON output.

### Agents

Agent set from docs and `ai_service/service.py`:

- `mentor_agent`
- `content_generator_agent`
- `analytics_agent`
- `career_advisor_agent`
- `motivation_agent`

Routing is heuristic based on message terms, weak topics, and roadmap progress. The mentor agent is always included. Outputs are synthesized into a single response with explainability metadata.

### Prompt Chains

Prompt builders are in `ai_service/prompts.py`:

- roadmap prompt.
- mentor chat prompt.
- specialist agent prompt.
- multi-agent synthesis prompt.
- progress analysis prompt.
- topic explanation prompt.
- question generation prompt.

### Memory

AI mentor responses include a `memory_update` payload. Backend mentor memory models exist:

- `mentor_memory_profiles`
- `mentor_session_memories`

Persistent AI memory implementation is partial. Dedicated vector memory: Not found.

### Retrieval

Retrieval-augmented generation/vector search: Not found.

### Embeddings

Embedding generation/storage: Not found.

### Recommendation Systems

Implemented:

- Rule-based recommendation engine.
- Content recommendation engine.
- ML recommendation engine scaffold.
- Roadmap prioritization.

### Digital Twin

Implemented as computed state, not as a separate persisted twin state machine. Uses roadmap progression, topic scores, retention data, learning events, ML feature snapshots, simulations, and predictive risk logic.

### Knowledge Graph

Implemented through topic prerequisite graph, knowledge graph engine, skill graph engine, topic graph/index services.

### Autonomous Agents

Docs and backend mention autonomous learning agent service. Mentor agent status/run endpoints exist. Fully autonomous execution loops with tool use beyond the product domain: Not found.

## 11. ML Analysis

### Models

Model registry table exists: `ml_model_registry`.

ML model artifacts: Not found.

### Datasets

Training dataset export scripts: Not found.

Data sources identified:

- `learning_events`
- `user_answers`
- `topic_scores`
- roadmap completion data
- question difficulty
- ML feature snapshots

### Training

Training metadata API exists: `POST /ml/train`.

Offline training scripts under `scripts/ml/`: Not found.

### Inference

Inference APIs:

- `GET /ml/infer/recommendations`
- `GET /ml/infer/difficulty/{topic_id}`
- `GET /ml/infer/dropout`

### Evaluation

Metrics fields in model registry/training run models are present. Evaluation pipeline implementation: Not found.

### Versioning

Versioning via `ml_model_registry` and `ml_training_runs`.

### Feature Store

`ml_feature_snapshots` is the lightweight feature store.

### Experiments

Experiment and experiment variant models exist, plus `ExperimentEngine`. ML-vs-rule rollout is documented, but production rollout execution evidence is partial.

### Retraining

Periodic retraining jobs: Not found.

## 12. System Architecture

### Overall

```mermaid
flowchart LR
    U[Users] --> FE[Next.js Frontend]
    U --> LP[Premium Landing]
    FE --> FG[Nginx Frontend Gateway]
    FG --> API_GW[Nginx API Gateway]
    API_GW --> API[FastAPI Backend]
    API --> PG[(PostgreSQL)]
    API --> Redis[(Redis)]
    API --> Celery[Celery Workers]
    Celery --> PG
    Celery --> Redis
    API --> AI[AI FastAPI Service]
    AI --> LLM[Groq/OpenAI-compatible Providers]
    API --> Kafka[(Kafka optional)]
    API --> S3[(S3-compatible storage optional)]
    Prom[Prometheus] --> API
    Prom --> NginxExporter[Nginx Exporter]
    Grafana[Grafana] --> Prom
    Alertmanager[Alertmanager] --> Prom
```

### Backend Request Lifecycle

```mermaid
sequenceDiagram
    participant Browser
    participant Nginx
    participant FastAPI
    participant Middleware
    participant Route
    participant Service
    participant Engine
    participant Repo
    participant DB

    Browser->>Nginx: HTTP request
    Nginx->>FastAPI: proxied request
    FastAPI->>Middleware: CORS/security/CSRF/rate/tenant/logging
    Middleware->>Route: request context
    Route->>Service: validated schema + auth context
    Service->>Engine: business decision
    Service->>Repo: persistence command/query
    Repo->>DB: SQLAlchemy async query
    DB-->>Repo: rows
    Repo-->>Service: models
    Service-->>Route: result DTO
    Route-->>Browser: response
```

### AI

```mermaid
flowchart TD
    API[Backend mentor/topic/roadmap route] --> AIC[AI Service Client]
    AIC --> AIS[AI Service Orchestrator]
    AIS --> Guard[Sanitize + Injection Hints]
    Guard --> RouteAgents[Route Specialist Agents]
    RouteAgents --> Mentor[Mentor Agent]
    RouteAgents --> Content[Content Generator]
    RouteAgents --> Analytics[Analytics Agent]
    RouteAgents --> Career[Career Advisor]
    RouteAgents --> Motivation[Motivation Agent]
    Mentor --> Synth[Synthesis Prompt]
    Content --> Synth
    Analytics --> Synth
    Career --> Synth
    Motivation --> Synth
    Synth --> LLM[OpenAI-compatible LLM]
    LLM --> AIS
    AIS --> API
```

### Deployment

```mermaid
flowchart LR
    GH[GitHub Actions] --> Verify[Verify/Build]
    Verify --> Images[GHCR Images]
    Images --> K8s[Kubernetes Manifests]
    K8s --> API[API Deployment]
    K8s --> FE[Frontend Deployment]
    K8s --> AI[AI Service Deployment]
    K8s --> Workers[Worker/Beat Deployments]
    K8s --> Ingress[Ingress]
```

## 13. DevOps Analysis

### Docker

`docker-compose.yml` defines:

- `frontend`
- `frontend_app`
- `landing`
- `api`
- `postgres`
- `redis`
- `mailpit`
- `celery_worker`
- `celery_beat`
- `ai_service`
- `nginx`
- `nginx_exporter`
- `prometheus`
- `alertmanager`
- `grafana`

Compose has 15 service keys, including gateway/frontends, landing page, API, database/cache/mail, workers, AI service, monitoring, and alerting.

### CI/CD

GitHub workflows:

- `ci.yml`: backend selected tests, frontend lint/test/build.
- `deploy.yml`: verify, build/push API/frontend/AI images to GHCR, deploy K8s manifests.
- `role-panel-smoke.yml`: Docker smoke checks for role panels and multitenancy.

Potential issue found in `deploy.yml`: API image build uses `file: Dockerfile` at repository root, but the backend Dockerfile is `backend/Dockerfile`. Root `Dockerfile`: Not found in file inventory. This likely breaks deploy image build unless another root Dockerfile exists outside inspected files. Status: risk.

### Monitoring

- Prometheus config and alert rules.
- Grafana datasource and platform overview dashboard.
- Alertmanager config.
- API `/metrics`.
- Nginx exporter.

### Logging

- Structured logging helpers.
- Request logging middleware.
- Audit log file path/rotation config.
- Logs mounted in Docker Compose.

### Metrics/Alerting

Prometheus alerts include API error/latency and outbox health according to docs and alert config.

### Redis/Celery/Kafka

- Redis used for cache, Celery broker/result backend, realtime pubsub.
- Celery worker and beat services exist.
- Kafka client/topic/schema registry scaffolding exists and is configurable.
- Kafka is optional and disabled by default.

### Secrets

- `.env` expected.
- `k8s/secrets.example.yaml` exists.
- Production config validates strong JWT secret and secure cookies.
- Real secrets: Not found in report; no secret values included.

### Backups/DR

Docs/scripts:

- `backend/scripts/ops/backup_db.sh`
- `backend/scripts/ops/restore_db.sh`
- `backend/scripts/ops/failover_cutover.sh`
- `docs/reliability_runbook.md`

Automated cloud backup execution: Not found.

## 14. Security Audit

### Strengths

- JWT access/refresh token separation.
- Session validation and token blacklist.
- Password hashing with bcrypt.
- Password strength validation requires letter, number, special character, and length.
- MFA TOTP helpers/routes.
- Role-based access and permission-based dependency.
- Dynamic authorization policy model.
- CSRF middleware for cookie-authenticated mutating requests.
- Security headers middleware with CSP, HSTS, frame denial, no-sniff, referrer policy.
- Rate limiting with SlowAPI/Redis.
- Tenant context middleware and RLS scripts.
- Production settings reject weak secrets/insecure cookie settings.
- Tests for security hardening, tenant isolation, RLS context, question serialization.

### Risks / Findings

1. Current backend tests fail: 28 failed, 334 passed, 1 skipped under dummy env.
2. Some authz tests indicate forbidden student access did not raise in direct function-call tests for audit and feature flags.
3. Test expectations and implementation are drifting in authorization/auth context, feature flags, audit export, tenant membership, cache, and roadmap service.
4. RLS coverage test cannot locate SQL scripts when run from `backend/` working directory.
5. Full database RLS enforcement was not verified against a running PostgreSQL instance in this pass.
6. Websocket authentication was not evident from route decorator extraction.
7. Centralized audit logging is not implemented; docs note audit storage is file-based.
8. SSO/OIDC/SAML: Not found.
9. Payment/billing security controls: Not found.
10. File antivirus/malware scanning: Not found.
11. Secrets manager integration: Not found, beyond env/K8s secret manifests.

## 15. Business Analysis

### Business Model

Documented model:

- Free tier for individual acquisition.
- Pro tier at `$19-$39/user/month`.
- Team/cohort tier at `$149-$499/month` base plus seats.
- Enterprise annual contracts.
- Usage-based add-ons for AI/API/marketplace/interview simulation.

### Target Customers

- Individual learners.
- Bootcamps/cohort programs.
- Schools/universities.
- Enterprise learning teams.

### Revenue

Primary:

- Subscriptions.

Secondary:

- AI overages.
- Seat expansion.
- Enterprise implementation.
- Marketplace take rate.
- API/ecosystem partnerships.

### Competitive Advantage

- Diagnostics-to-roadmap loop.
- Multi-role SaaS.
- AI mentor with memory direction.
- Career readiness and job-readiness framing.
- Knowledge graph/ML/digital twin architecture.
- Operational tenant-aware backend foundations.

### Go-To-Market

Documented:

- SEO around career/learning intent.
- Demo-led social content.
- Campus ambassadors and creator-teachers.
- Bootcamp/cohort partnerships.
- Product-led sharing of readiness/resume artifacts.

### Market Position

Positioned as an AI-native learning and career platform, not merely an LMS.

## 16. Product Maturity Scores

| Area | Score | Evidence |
|---|---:|---|
| Architecture maturity | 8 | Clear layered backend, modular services, repositories, engines, migrations, infra assets |
| Product maturity | 6 | Broad feature surface and role panels; frontend parity and test health lag |
| Code quality | 6 | Strong structure, many tests; current failing tests and contract drift reduce confidence |
| Scalability | 7 | Async API, Redis/Celery, outbox, indexes, K8s/HPA/PDB; DB/RLS validation incomplete |
| Security | 6 | Good security middleware/auth foundation; authz/RLS tests not clean, SSO absent |
| Maintainability | 7 | Clean module boundaries, docs, tests; large surface area and some broken tests |
| Production readiness | 6 | Compose/K8s/monitoring exist; failing tests and deploy workflow risk remain |
| Enterprise readiness | 5 | Multi-tenancy, roles, audit/RLS; no SSO, billing, centralized audit, proven DR |
| Technical debt | 5 | Test drift, partial ML/AI, partial RLS, broad unfinished modules |
| Innovation score | 8 | Diagnostics, knowledge graph, digital twin, multi-agent AI, ML platform foundations |

## 17. Verification Results From This Pass

### Backend

Command:

```bash
cd backend
pytest -q
```

Result:

- Failed immediately because `pytest` was not on shell `PATH`.

Command:

```bash
cd backend
../.venv/bin/pytest -q
```

Result:

- 46 collection errors because `DATABASE_URL` and `JWT_SECRET` were not set.
- 1 skipped due to missing `openai` package in that virtualenv.

Command:

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/learning_platform \
JWT_SECRET=test-secret-with-enough-length-123456789 \
AUTH_COOKIE_SECURE=false \
../.venv/bin/pytest -q
```

Result:

- 334 passed.
- 28 failed.
- 1 skipped.

Representative failures:

- Audit ops route authorization/export fake contract drift.
- Authorization service `AuthContext` constructor mismatch in tests.
- Feature flag forbidden/update tests failing.
- Goal/graph/roadmap/cache service contract drift.
- Job/RLS tests using repository-root paths while executed from `backend/`.
- Security hardening test expects alphanumeric password accepted, implementation now requires special character.
- Tenant membership tests expect `validate_tenant_membership`, implementation has `require_tenant_membership`.
- Transaction rollback tests failing due changed password rule and dummy session contract.

### Frontend

Command:

```bash
cd learning-platform-frontend
npm run test:run
```

Result:

- 7 test files passed.
- 2 test files failed.
- 20 tests passed.
- 2 tests failed.

Failures:

- `app/(student)/student/dashboard/page.test.tsx`
- `app/(student)/student/mentor/page.test.tsx`

Reason:

- `useAuthContext must be used within AuthProvider`.

## 18. Missing / Not Found Inventory

- Dedicated settings page: Not found.
- SSO/OIDC/SAML: Not found.
- Payment processor integration: Not found.
- Billing enforcement around subscription plans: Not found.
- Serialized ML model artifacts: Not found.
- Offline ML training scripts under `scripts/ml/`: Not found.
- Embeddings/vector store/RAG pipeline: Not found.
- Centralized audit log storage: Not found.
- Dedicated trigger inventory: Not found.
- Antivirus/malware scanning for uploads: Not found.
- Root `Dockerfile` referenced by deploy workflow: Not found.
- Production cloud environment definitions beyond K8s manifests/scripts: Not found.
- Automated recurring backup scheduler in manifests: Not found, though backup scripts and runbook exist.

## 19. Due Diligence Summary

This project is a serious backend-heavy SaaS platform with meaningful product breadth and a coherent technical architecture. It is not just a landing page or prototype. The strongest areas are backend domain modeling, diagnostics, roadmaps, multi-tenancy architecture, operational outbox design, documentation, and deployment/monitoring assets.

The largest diligence risks are current automated test failures, incomplete frontend/backend parity, partially proven tenant isolation, partial AI/ML maturity, and enterprise gaps such as SSO, centralized audit logging, billing enforcement, and fully verified disaster recovery.

Recommended priority order:

1. Fix backend and frontend test suites until CI is green.
2. Fix `deploy.yml` Dockerfile path risk.
3. Run RLS coverage and integration tests from repository root against real PostgreSQL.
4. Close authz regressions around audit/feature flag forbidden access.
5. Decide which AI/ML features are production commitments versus roadmap.
6. Add SSO, billing enforcement, centralized audit logging, and file scanning if enterprise readiness is required.
