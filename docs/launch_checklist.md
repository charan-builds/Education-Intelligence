# Launch Checklist

Use this checklist before calling the platform launch-ready.

## 1. Environment
- Copy `.env.example` to `.env`
- Set real values for:
  - `DATABASE_URL`
  - `REDIS_URL`
  - `SECRET_KEY`
  - `CORS_ORIGINS`
  - `AUDIT_LOG_FILE_PATH`
  - `GRAFANA_ADMIN_PASSWORD`
- Copy frontend env:
  - `learning-platform-frontend/.env.local`
  - set `NEXT_PUBLIC_API_URL`

## 2. Database
- Run migrations:
  - `alembic upgrade head`
- Seed baseline content if needed:
  - `python scripts/bootstrap_seed.py`
- Confirm at least one tenant and one goal exist for learner flows

## 3. Verification
- Preflight machine checks:
  - `make preflight`
- Backend:
  - `make verify-backend`
- Frontend:
  - `make verify-frontend`
- API smoke:
  - start backend first
  - `make smoke`
- Multi-tenant content smoke:
  - start backend first
  - `make smoke-multitenant`
- Browser E2E:
  - start backend first
  - `cd learning-platform-frontend && npx playwright install chromium`
  - `E2E_API_URL=http://127.0.0.1:8000 npm run test:e2e`

## 4. Docker
- Run:
  - `docker compose up --build`
- Default host bindings:
  - Postgres on `127.0.0.1:5433`
  - Redis on `127.0.0.1:6380`
  - override with `POSTGRES_HOST_PORT` / `REDIS_HOST_PORT` if those are already in use
- Confirm services:
  - frontend on `:3000`
  - nginx/api on `:8000`
  - prometheus on `:9090`
  - grafana on `:3001`
  - alertmanager on `:9093`
- Confirm `./logs` is being written to by API/Celery services

## 5. Security
- Replace example secrets
- Restrict `CORS_ORIGINS` to real frontend domains
- Review feature flags enabled per tenant
- Confirm rate limiting is active on auth and audit endpoints

## 6. Observability
- Confirm structured logs are emitted
- Confirm audit log rotation is working
- Confirm `/metrics` is scraped by Prometheus
- Confirm Grafana dashboards load
- Confirm alert rules are visible in Prometheus/Alertmanager

## 7. Product Flow
- Register a student
- Log in
- Log in as each seeded panel role:
  - `student`
  - `teacher`
  - `mentor`
  - `admin`
  - `super_admin`
- Select a goal
- Start diagnostic
- Submit diagnostic
- Generate roadmap
- Open topic page
- Update roadmap progress
- View teacher/admin summaries
- Log in as each seeded tenant admin and confirm goals/topics differ per organization

## 8. Known Remaining Gaps
- Audit storage is file-based, not centralized
- Browser E2E still depends on seeded tenant/goal assumptions
- Teacher analytics are tenant-wide, not cohort-based
