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
- `DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/learning_platform`
- `REDIS_URL=redis://localhost:6379`
- `SECRET_KEY=supersecret`
- `ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`

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

## Docker (API + Gateway + DB + Redis + Worker)
```bash
docker compose up --build
```

Gateway entrypoint:
- `http://localhost:8000` -> Nginx -> FastAPI

Notes:
- API container is internal-only in compose; Nginx is the public edge.
- Nginx config includes gzip, request rate limiting, forwarded headers, and SSL-ready template config.
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
- `GET /ops/feature-flags/catalog` (admin/super_admin; supported flag names)
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
