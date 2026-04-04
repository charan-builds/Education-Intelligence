# Universal Learning Intelligence Platform

A production-oriented, multi-tenant SaaS platform that identifies learner knowledge gaps, runs diagnostics, generates personalized roadmaps, and tracks progress across institutions and independent learners.

## Overview

Universal Learning Intelligence Platform is designed to move learning from static course delivery to adaptive, intelligence-driven progression.

The platform helps:

- students understand what they know and what they need next
- teachers monitor cohort risk and weak-topic clusters
- institution admins manage users, goals, content, and analytics
- platform operators manage tenants and cross-tenant performance
- independent learners use a personal learning workspace

At its core, the system turns assessment signals into actionable learning plans:

`Diagnostic Test -> Topic Scores -> Weak Topics -> Prerequisites -> Personalized Roadmap`

## Core Capabilities

- Multi-tenant SaaS architecture
- JWT authentication with refresh sessions
- Role-based access control
- Adaptive diagnostic testing
- Rule-based recommendation engine
- Personalized roadmap generation
- Roadmap progress tracking
- Learner, tenant, and platform analytics
- Background jobs with Celery
- Outbox-based async reliability
- Monitoring with Prometheus and Grafana
- Docker Compose and Kubernetes deployment assets

## Panels

- **Super Admin Panel**
  - Tenant oversight, platform analytics, outbox visibility, health-oriented controls

- **Institution Admin Panel**
  - User management, topic/question/goal management, analytics, moderation, feature controls

- **Teacher Panel**
  - Cohort analytics, weak-topic tracking, retention visibility, watchlists

- **Student Panel**
  - Authentication, diagnostics, results, roadmap generation, progress tracking, learner dashboard

- **Independent Learner Panel**
  - Personal workspace path built on the learner journey with tenant type support for personal accounts

## Architecture

The backend follows a layered architecture:

`Route -> Service -> Engine -> Repository -> Database`

### Backend layers

- **Presentation**
  - FastAPI route handlers and schemas

- **Application services**
  - Use-case orchestration such as auth, diagnostics, roadmaps, analytics, dashboards, and notifications

- **Domain engines**
  - Adaptive testing, recommendation, prerequisite tracing, knowledge graph reasoning, weakness modeling, learning profile analysis

- **Infrastructure**
  - Async database access, repositories, Redis, Celery, monitoring, and streaming support

### Key services

- `DiagnosticService`
  - manages the test lifecycle, answer scoring, resume state, and completion flow

- `RecommendationService`
  - selects weak topics and prerequisite-backed learning targets

- `RoadmapService`
  - transforms diagnostic results into prioritized roadmap steps

- `AnalyticsService`
  - exposes learner, tenant, topic, and platform-level metrics

## Tech Stack

### Backend

- Python 3.11+
- FastAPI
- SQLAlchemy async ORM
- Alembic
- Celery
- Redis

### Database

- PostgreSQL

### Frontend

- Next.js
- React 19
- TypeScript
- React Query

### Ops

- Docker Compose
- Kubernetes manifests
- Nginx
- Prometheus
- Grafana
- Alertmanager

## Repository Structure

```text
.
├── backend/                    # FastAPI backend, domain logic, repositories, tests
├── learning-platform-frontend/ # Next.js frontend
├── ai_service/                 # Separate AI service scaffold
├── docs/                       # Architecture, deployment, and audit docs
├── k8s/                        # Kubernetes manifests
├── monitoring/                 # Prometheus, Grafana, Alertmanager
├── nginx/                      # Gateway and frontend routing config
├── docker-compose.yml          # Local full-stack environment
└── blueprint.md                # Detailed project documentation and progress audit
```

## Key Data Model

Core tables include:

- `tenants`
- `users`
- `goals`
- `topics`
- `topic_prerequisites`
- `questions`
- `diagnostic_tests`
- `user_answers`
- `roadmaps`
- `roadmap_steps`

This relational design supports:

- strong tenant ownership boundaries
- topic graph traversal and prerequisite reasoning
- diagnostic scoring history
- personalized roadmap generation
- analytics and auditability

## Current Project Status

This repository is beyond a prototype. The backend is substantial and production-oriented, while frontend maturity varies by panel.

### Completed

- FastAPI modular backend
- JWT auth, refresh, invite, reset, verification, MFA support
- Tenant and user management APIs
- Topic, question, prerequisite, and goal management
- Adaptive diagnostic flow
- Rule-based recommendations
- Roadmap generation and roadmap step updates
- Student dashboard and learner flow
- Admin dashboard foundations and management workflows
- Async jobs, outbox reliability, and monitoring stack
- Docker Compose and Kubernetes deployment assets
- Strong backend test coverage

### Partially Completed

- Full database-wide tenant isolation via PostgreSQL RLS
- Analytics freshness and operational hardening
- Teacher workflow depth
- Independent learner UX differentiation
- Mentor and AI-assisted workflows
- Full frontend parity for every backend feature
- ML-driven recommendation maturity

### Not Fully Implemented Yet

- Fully validated ML recommendation pipeline as default production path
- Complete RLS coverage across all tenant-aware tables
- Fully distinct UI coverage across every role and workflow

## Production Readiness Notes

The platform has strong production foundations:

- layered backend architecture
- background jobs and retry patterns
- rate limiting and security middleware
- Prometheus metrics and Grafana dashboards
- Nginx gateway and containerized deployment
- health endpoints and observability hooks

The biggest remaining production gap is tenant-isolation hardening. PostgreSQL RLS exists for part of the schema, but some flows still rely on manual tenant filters in repositories and services.

## Local Development

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[test]
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

## Frontend Setup

```bash
cd learning-platform-frontend
npm install
npm run dev
```

## Full Local Stack

From the repository root:

```bash
docker compose up --build
```

Useful local endpoints:

- API gateway: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`

## Seeded Demo Accounts

The repository includes seeded demo users for platform and tenant-level testing, including:

- super admin
- admin
- teacher
- mentor
- student

See [backend/README.md](/home/charan_derangula/projects/intelligentSystems/backend/README.md) for current seeded credentials and local bootstrap details.

## Verification

Project-level shortcuts:

```bash
make preflight
make verify-backend
make verify-frontend
make verify
make smoke
make smoke-multitenant
```

### Audit verification completed

During the latest audit, a focused backend verification passed:

- auth routes
- diagnostic routes
- roadmap routes
- analytics routes

Result:

- `27 passed`

## Deployment

The repository includes:

- Docker Compose for local and demo environments
- Kubernetes manifests for API, frontend, AI service, workers, ingress, autoscaling, and network policies
- Monitoring stack configuration
- CI/CD workflow references

See:

- [docs/production-deployment.md](/home/charan_derangula/projects/intelligentSystems/docs/production-deployment.md)
- [docs/global_deployment_architecture.md](/home/charan_derangula/projects/intelligentSystems/docs/global_deployment_architecture.md)

## Security

- JWT access and refresh tokens
- bcrypt password hashing
- role-based access control
- tenant-aware repository access
- partial PostgreSQL row-level security rollout
- rate limiting and security middleware

## Strengths

- Clean architecture and strong separation of concerns
- Serious backend depth for diagnostics, roadmaps, analytics, and auth
- Multi-tenant design built into the core data model
- Good operational foundations for scaling and observability
- Strong base for extending into ML, AI mentoring, and advanced analytics

## Gaps and Risks

- Full RLS enforcement is not complete across all tenant-scoped tables
- Analytics can depend on snapshot rebuild timing
- Some panels are ahead in backend capability but behind in polished UX
- ML recommendation exists as an extension path, not yet as the primary proven production flow

## Documentation

- [blueprint.md](/home/charan_derangula/projects/intelligentSystems/blueprint.md) - full project documentation and audit report
- [backend/README.md](/home/charan_derangula/projects/intelligentSystems/backend/README.md) - backend-specific setup and operational details
- [docs/learning_intelligence_platform_architecture.md](/home/charan_derangula/projects/intelligentSystems/docs/learning_intelligence_platform_architecture.md)
- [docs/production-deployment.md](/home/charan_derangula/projects/intelligentSystems/docs/production-deployment.md)

## Elevator Pitch

Universal Learning Intelligence Platform is a multi-tenant learning SaaS that converts learner assessment data into personalized roadmaps, analytics, and next-step recommendations for institutions and independent learners.
