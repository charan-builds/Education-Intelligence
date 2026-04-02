# Learning Intelligence Platform Backend

Production-ready backend MVP for a multi-tenant learning intelligence SaaS.

## Stack
- Python 3.11+
- FastAPI
- PostgreSQL (asyncpg)
- SQLAlchemy (async ORM)
- Alembic
- JWT auth + bcrypt hashing
- Pydantic + pydantic-settings
- Pytest

## Architecture
Clean architecture modular monolith:
- `presentation` -> API routes only
- `application` -> use-case services
- `domain` -> entities + core engines (infra-agnostic)
- `infrastructure` -> DB/session/repositories

Distributed target architecture:
- see [docs/distributed_system_architecture.md](/home/charan_derangula/projects/intelligentSystems/docs/distributed_system_architecture.md)

Global deployment target:
- see [docs/global_deployment_architecture.md](/home/charan_derangula/projects/intelligentSystems/docs/global_deployment_architecture.md)

Business strategy:
- see [docs/business_strategy.md](/home/charan_derangula/projects/intelligentSystems/docs/business_strategy.md)

Multi-agent AI architecture:
- see [docs/multi_agent_ai_architecture.md](/home/charan_derangula/projects/intelligentSystems/docs/multi_agent_ai_architecture.md)

Digital twin architecture:
- see [docs/digital_twin_architecture.md](/home/charan_derangula/projects/intelligentSystems/docs/digital_twin_architecture.md)

Next-generation platform vision:
- see [docs/next_generation_intelligent_learning_platform.md](/home/charan_derangula/projects/intelligentSystems/docs/next_generation_intelligent_learning_platform.md)

Rules enforced:
- Routes do not access DB directly.
- Business logic is in services.
- Database logic is only in repositories.
- Tenant-owned queries are tenant-scoped.

## Project Structure
See `app/` modules for:
- Auth, tenants, users
- Diagnostic test lifecycle
- Rule-based recommendation engine
- Recursive prerequisite tracer
- Roadmap generation

## Environment
Copy and update env vars:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/learning_platform`
- `REDIS_URL=redis://redis:6379/0`
- `CELERY_BROKER_URL=redis://redis:6379/0`
- `CELERY_RESULT_BACKEND=redis://redis:6379/0`
- `POSTGRES_HOST_PORT=5433` for host access to the Compose Postgres container
- `REDIS_HOST_PORT=6380` for host access to the Compose Redis container
- `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`
- `JWT_SECRET=<generate-a-long-random-secret>`
- `ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `DEFAULT_TENANT_ID=1`
- `AUDIT_LOG_MAX_BYTES=10485760`
- `AUDIT_LOG_BACKUP_COUNT=5`
- `AUDIT_LOG_READ_MAX_LINES=50000`

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -e .[test]
```

## Migrations
```bash
alembic upgrade head
```

## Run API
```bash
uvicorn app.main:app --reload
```

Seed local defaults:
```bash
python seed.py
```

Seeded credentials:
- platform tenant: `Platform`
- super admin: `superadmin@platform.example.com` / `SuperAdmin123!`
- tenant: `Demo University`
- tenant_id: `1`
- student panel: `student@example.com` / `Student123!`
- teacher panel: `teacher@example.com` / `Teacher123!`
- mentor panel: `mentor@example.com` / `Mentor123!`
- admin panel: `admin@example.com` / `admin123`

Additional demo tenant users:
- tenant: `Northwind School`
  - student: `student@northwind.local` / `Student123!`
  - teacher: `teacher@northwind.local` / `Teacher123!`
  - mentor: `mentor@northwind.local` / `Mentor123!`
  - admin: `admin@northwind.local` / `admin123`
- tenant: `Acme Learning Co`
  - student: `student@acme.local` / `Student123!`
  - teacher: `teacher@acme.local` / `Teacher123!`
  - mentor: `mentor@acme.local` / `Mentor123!`
  - admin: `admin@acme.local` / `admin123`

## Docker (API + Gateway + DB + Redis + Worker)
```bash
docker compose up --build
```

## Kubernetes / Cloud Deployment

Production-oriented Kubernetes manifests live in:

- [k8s/namespace.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/namespace.yaml)
- [k8s/configmap.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/configmap.yaml)
- [k8s/secrets.example.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/secrets.example.yaml)
- [k8s/api.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/api.yaml)
- [k8s/frontend.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/frontend.yaml)
- [k8s/ai-service.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/ai-service.yaml)
- [k8s/workers.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/workers.yaml)
- [k8s/ingress.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/ingress.yaml)
- [k8s/hpa.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/hpa.yaml)
- [k8s/pdb.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/pdb.yaml)
- [k8s/network-policy.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/network-policy.yaml)
- [k8s/cronjobs.yaml](/home/charan_derangula/projects/intelligentSystems/k8s/cronjobs.yaml)

CI/CD deployment workflow:

- [.github/workflows/deploy.yml](/home/charan_derangula/projects/intelligentSystems/.github/workflows/deploy.yml)

Gateway entrypoint:
- `http://localhost:8000` -> Nginx -> FastAPI
- `http://localhost:3000` -> Next.js frontend

Notes:
- API container is internal-only in compose; Nginx is the public edge.
- Frontend runs as a separate container and talks to the API gateway through `NEXT_PUBLIC_API_URL`.
- API startup automatically runs Alembic migrations and only seeds when `RUN_SEED_ON_STARTUP=true` before starting Gunicorn.
- Automatic startup seeding is disabled by default in Docker; set `RUN_SEED_ON_STARTUP=true` only for intentional demo/bootstrap environments.
- Compose binds Postgres to `127.0.0.1:5433` and Redis to `127.0.0.1:6380` by default to avoid conflicts with local developer services. Override with `POSTGRES_HOST_PORT` or `REDIS_HOST_PORT` if needed.
- `docker compose up` credentials from `scripts/bootstrap_seed.py`:
  - `superadmin@platform.example.com` / `SuperAdmin123!`
  - `admin@platform.example.com` / `Admin123!`
  - `teacher@platform.example.com` / `Teacher123!`
  - `mentor@platform.example.com` / `Mentor123!`
  - `student@platform.example.com` / `Student123!`
- Nginx config includes gzip, request rate limiting, forwarded headers, and SSL-ready template config.
- `./logs` is mounted into API and Celery containers so rotating audit/application logs persist outside container restarts.
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001` (defaults from `.env.example`)

## AI Service
Separate FastAPI service at `ai_service/` for future model hosting.

Endpoints:
- `POST /predict-learning-path`
- `POST /mentor-response`
- `GET /health`

In compose, backend reaches it via:
- `AI_SERVICE_URL=http://ai_service:8100`

## Outbox Reliability
- When immediate Celery dispatch fails, task payloads are persisted in `outbox_events`.
- Replay task:
  - `jobs.process_outbox_events`
- This allows eventual dispatch after broker recovery without dropping events.
- `celery_beat` runs this replay automatically every minute in Docker Compose.
- `jobs.refresh_outbox_metrics` runs every minute to keep queue depth gauges current.
- `jobs.recover_stuck_outbox_events` runs every 5 minutes to requeue stale `processing` events.
- Failed events retry with delay and move to `dead` status after max attempts.
- Cleanup task:
  - `jobs.cleanup_outbox_events` runs daily and removes old `dispatched`/`dead` events.
- Ops endpoints:
  - `GET /ops/outbox` (admin/super_admin)
  - `GET /ops/outbox/stats` (admin/super_admin)
  - `POST /ops/outbox/flush` (admin/super_admin)
  - `POST /ops/outbox/requeue-dead` (admin/super_admin)
  - `POST /ops/outbox/requeue-dead/{event_id}` (admin/super_admin)
  - `POST /ops/outbox/recover-stuck` (admin/super_admin)
- Outbox statuses include: `pending`, `processing`, `dead`, `dispatched`.

## Monitoring
- API metrics endpoint: `GET /metrics`
- Prometheus scrapes:
  - `api:8000/metrics`
  - `nginx_exporter:9113/metrics`
- Prometheus alert rules:
  - high API error rate
  - high p95 latency
  - outbox dispatch success ratio degradation
  - outbox dispatch failure spikes
  - outbox dead-letter growth
  - outbox pending/dead backlog thresholds
- Alertmanager endpoint: `http://localhost:9093`
- Grafana is pre-provisioned with:
  - Prometheus datasource
  - `Learning Platform Overview` dashboard

## Ops APIs
- `GET /ops/feature-flags` (admin/super_admin; tenant-scoped for admin)
- `GET /ops/feature-flags` accepts `limit` and `offset`, and returns pagination metadata (`limit`, `offset`, `returned`, `total`, `has_more`, `next_offset`)
- `GET /ops/feature-flags`, `GET /ops/feature-flags/catalog`, and `POST /ops/feature-flags/{flag_name}` are rate-limited per-user and per-IP
- `GET /ops/feature-flags` supports ETag and cache headers (`Cache-Control`, `Vary`)
- `GET /ops/feature-flags/catalog` (admin/super_admin; supported flag names)
  - supports ETag and cache headers (`Cache-Control`, `Vary`)
- `POST /ops/feature-flags/{flag_name}` (admin/super_admin; tenant-scoped for admin)
  - returns `400` for unsupported flag names
- `GET /ops/audit/feature-flags` (admin/super_admin; tenant-scoped for admin)
  - supports `limit`, `offset`, `since`, `until`, `feature_name`, `order` query params
  - response includes `meta` (`limit`, `offset`, `returned`, `has_more`, `next_offset`)
- `GET /ops/audit/feature-flags/export` (admin/super_admin; CSV export with same filters)
  - response headers include `X-Export-Row-Count` and `X-Export-SHA256`
  - pagination headers include `X-Export-Has-More` and `X-Export-Next-Offset`
  - both endpoints are rate-limited per-user and per-IP
  - returns `400` when `since > until`
  - returns `400` when lookback exceeds `AUDIT_MAX_LOOKBACK_DAYS`
- `GET /ops/audit/feature-flags/names` (admin/super_admin; distinct feature names for filter UIs)
  - supports ETag and cache headers (`Cache-Control`, `Vary`)
  - returns `400` for invalid `since/until` or lookback beyond `AUDIT_MAX_LOOKBACK_DAYS`

## Test
```bash
pytest -q
```

Project-level verification shortcuts:

```bash
make preflight
make verify-backend
make verify-frontend
make verify
make smoke
make smoke-multitenant
```

Frontend unit/integration tests:

```bash
cd learning-platform-frontend
npm run test:run
```

Browser E2E learner journey:

```bash
cd learning-platform-frontend
npx playwright install chromium
E2E_API_URL=http://127.0.0.1:8000 npm run test:e2e
```

Notes:
- The E2E test starts the Next.js frontend automatically.
- The FastAPI backend must already be running and seeded with at least one valid goal.
- Default E2E assumptions:
  - `E2E_TENANT_ID=1`
  - `E2E_GOAL_ID=1`

Multi-tenant smoke verification:

```bash
make smoke-multitenant
```

This verifies the seeded demo organizations can each log in and only see their tenant-owned goals/topics through the real API.

Launch checklist:
- see [docs/launch_checklist.md](/home/charan_derangula/projects/intelligentSystems/docs/launch_checklist.md)

## Frontend Route Map

Primary entry routes:
- `/`
- `/auth`
- `/dashboard`
- `/diagnostic`
- `/goals`
- `/roadmap`

Role dashboards:
- `/dashboard/student`
- `/dashboard/teacher`
- `/dashboard/admin`
- `/dashboard/super-admin`

Learning flow:
- `/goals/select`
- `/diagnostic/test`
- `/diagnostic/result`
- `/roadmap/view`
- `/topic/{topicId}`
- `/progress`
- `/mentor`
- `/community`

Routing notes:
- parent routes (`/dashboard`, `/diagnostic`, `/goals`, `/roadmap`) redirect to the correct concrete page
- protected routes redirect unauthenticated users to `/auth?next=...`
- authenticated users hitting `/auth` are redirected to the intended `next` path or their role dashboard

## Implemented Endpoints
- `POST /auth/register`
- `POST /auth/login`
- `POST /tenants`
- `GET /tenants`
- `POST /users`
- `GET /users`
- `POST /diagnostic/start`
- `POST /diagnostic/submit`
- `GET /diagnostic/result`
- `POST /diagnostic/next-question`

Diagnostic scoring notes:
- Question correctness is now evaluated in the backend using `questions.correct_answer`
- Frontend no longer needs to calculate diagnostic scores locally
- `POST /roadmap/generate`
- `GET /roadmap/{user_id}`

## AI-Ready Expansion
Recommendation engine follows interface pattern:
- `RecommendationEngine` (contract)
- `RuleEngine` (current)
- `MLRecommendationEngine` (future)

This allows swapping strategy without breaking route/service contracts.

## Smoke Test (Full Flow)
Run the end-to-end API smoke flow:

```bash
make smoke
```

Flow covered:
- register
- login
- start diagnostic
- submit answers
- generate roadmap
- view roadmap

Optional env overrides:

```bash
BASE_URL=http://127.0.0.1:8000 SMOKE_TENANT_ID=1 SMOKE_GOAL_ID=1 make smoke
```

Run the seeded role-panel regression smoke flow:

```bash
make smoke-role-panels
```

Flow covered:
- student login, profile, goals, diagnostic, roadmap, mentor chat
- teacher analytics
- mentor analytics and suggestions
- admin users and analytics
- super-admin platform overview and outbox stats

Optional env override:

```bash
BASE_URL=http://127.0.0.1:8000 make smoke-role-panels
```

CI coverage:
- GitHub Actions now runs `.github/workflows/role-panel-smoke.yml`
- It starts the Docker-backed API stack and executes both `make smoke-role-panels` and `make smoke-multitenant`
- The two smoke checks run as separate jobs on pull requests, pushes to `main`/`master`, and manual dispatch
