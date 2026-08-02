# Folder Structure

This file gives a clean overview of the project structure, the essential folders, the testing tools in use, and the main work completed so far.

## Clean Repository Structure

```text
intelligentSystems/
├── backend/                        # FastAPI backend, business logic, DB access, tests
│   ├── alembic/                    # Database migrations
│   ├── app/
│   │   ├── application/           # Application services and use-case orchestration
│   │   ├── core/                  # Core config, security, shared utilities
│   │   ├── domain/                # Domain models, engines, and domain services
│   │   ├── events/                # Event-related logic
│   │   ├── infrastructure/        # Repositories, cache, jobs, monitoring, clients
│   │   ├── presentation/          # API routes, middleware, request/response handling
│   │   ├── realtime/              # Realtime hub and distributed bus
│   │   └── schemas/               # Pydantic schemas
│   ├── scripts/                   # Ops, chaos, and load/testing scripts
│   ├── sql/                       # SQL helpers and tenant/RLS scripts
│   └── tests/                     # Backend test suite
├── learning-platform-frontend/     # Next.js frontend application
│   ├── app/                       # App Router pages and role-based route groups
│   │   ├── (admin)/
│   │   ├── (auth)/
│   │   ├── (independent-learner)/
│   │   ├── (mentor)/
│   │   ├── (student)/
│   │   ├── (super-admin)/
│   │   └── (teacher)/
│   ├── components/                # Shared and role-specific UI components
│   ├── features/                  # Feature modules
│   ├── hooks/                     # Reusable React hooks
│   ├── lib/                       # Shared frontend helpers
│   ├── public/                    # Static assets
│   ├── services/                  # API/service layer
│   ├── store/                     # State/store setup
│   ├── stores/                    # Zustand stores
│   ├── tests/                     # Frontend test suites
│   │   └── e2e/                   # Playwright end-to-end tests
│   ├── types/                     # TypeScript types
│   └── utils/                     # Utility helpers
├── ai_service/                     # Separate AI service scaffold
├── docs/                           # Architecture, deployment, audit, and planning docs
├── k8s/                            # Kubernetes manifests
├── monitoring/                     # Prometheus, Grafana, Alertmanager
├── nginx/                          # Nginx gateway and frontend routing config
├── docker-compose.yml              # Local full-stack orchestration
├── Makefile                        # Common project commands
├── README.md                       # Main project overview
└── FOLDER_STRUCTURE.md             # This structure and project summary document
```

## Folders To Treat As Generated Or Non-Essential

These exist in the repo/workspace but are not part of the core source structure:

- `.git/`
- `.venv/`, `venv/`, `.venv-1/`
- `__pycache__/`
- `.pytest_cache/`
- `learning-platform-frontend/.next/`
- `learning-platform-frontend/node_modules/`
- `learning-platform-frontend/test-results/`
- `Premiumsaaslandingpage-main/` for separate landing page assets/reference work
- `logs/`

## Testing Used In This Project

### Backend testing

- `pytest`
- `pytest-asyncio`
- Test location: `backend/tests/`

Used for:

- service-layer tests
- route contract tests
- tenant-isolation and security checks
- roadmap, auth, diagnostics, jobs, outbox, and engine tests

### Frontend unit/integration testing

- `vitest`
- `@testing-library/react`
- `@testing-library/jest-dom`
- Test files are colocated in places like:
  - `learning-platform-frontend/app/**/*.test.tsx`
  - `learning-platform-frontend/services/*.test.ts`
  - `learning-platform-frontend/utils/*.test.ts`
  - `learning-platform-frontend/middleware.test.ts`

Used for:

- page rendering tests
- service tests
- utility logic tests
- middleware behavior tests

### Frontend end-to-end testing

- `playwright`
- Test location: `learning-platform-frontend/tests/e2e/`

Current e2e coverage includes flows such as:

- learner journey
- live onboarding
- live login
- tenant switching

## Main Things Already Done

The repository already includes the main foundations for a production-oriented learning platform:

- Multi-tenant SaaS architecture
- FastAPI backend with layered design
- Next.js frontend with role-based panels
- JWT authentication and session flows
- Role-based access control
- Tenant and user management
- Topic, question, goal, and prerequisite management
- Adaptive diagnostic testing flow
- Personalized roadmap generation
- Learner progress tracking
- Analytics and dashboard foundations
- Background jobs with Celery
- Redis integration
- Monitoring with Prometheus and Grafana
- Nginx gateway configuration
- Docker Compose setup
- Kubernetes deployment manifests
- AI service scaffold for future/extended AI workflows

## Major Product Areas In The Frontend

- Student panel
- Teacher panel
- Admin panel
- Super admin panel
- Mentor panel
- Independent learner panel
- Shared auth, dashboard, roadmap, diagnostic, community, and analytics flows

## Main Backend Architecture Pattern

The backend broadly follows:

```text
Route -> Service -> Engine -> Repository -> Database
```

This means:

- `presentation/` handles API entry points
- `application/` coordinates use cases
- `domain/` contains core rules and engines
- `infrastructure/` handles persistence and external systems

## Recommended Files To Read First

If someone is new to the project, start with:

- `README.md`
- `backend/README.md`
- `FOLDER_STRUCTURE.md`
- `docs/learning_intelligence_platform_architecture.md`
- `docs/production-deployment.md`
- `blueprint.md`
