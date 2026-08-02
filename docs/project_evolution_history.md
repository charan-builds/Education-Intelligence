# Project Evolution History

This document reconstructs the developmental progression of the **Learning Intelligence Platform** codebase, estimating historical phases based on the active directories, database schema versions, and architecture records.

---

## 1. Version 0: The Proof of Concept (MVP)

```text
[Client: Simple React SPA] ──(HTTP)──> [FastAPI Backend] ──> [Postgres (Single User Table)]
```

### Architectural Profile
*   **Backend**: A basic FastAPI process containing inline database operations.
*   **Frontend**: A simple React Single-Page Application (SPA) deployed to static web servers.
*   **Database**: Flat PostgreSQL tables with `users` and `topics`. No migration version controls, no tenant isolation, and no cache layers.

### Why It Was Built
To validate basic user interest, prove that the core HTTP service could handle logins, and confirm that static educational topics could render correctly in a browser.

---

## 2. Version 1: Structured Monolith & Personalized Roadmaps

```text
Next.js Client ──> FastAPI (Presentation -> Application -> Domain -> Infrastructure) 
                         ├── Prerequisite Traversal Engine
                         └── PostgreSQL (Alembic Migrations Active)
```

### Architectural Profile
*   **Backend**: Migrated to a clean layered structure (Presentation $\rightarrow$ Application $\rightarrow$ Domain $\rightarrow$ Infrastructure) to isolate business logic.
*   **Frontend**: Migrated to Next.js to leverage layouts and dynamic page routes.
*   **Database**: Alembic migrations environment initialized (`alembic/`). Schema tables expanded to include `goals`, `roadmap_steps`, `diagnostic_tests`, and `user_answers`.
*   **Domain Engines**: Introduced the [AdaptiveTestingEngine](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/adaptive_testing_engine.py) to assess user ability, and topological sorting algorithms to generate custom learning roadmaps.

### Why Features Were Introduced
*   *Layered Design*: Monolithic route files became too bloated; separating route handlers from database queries was necessary to keep the codebase maintainable.
*   *Adaptive Testing*: Standard questionnaires were not diagnostic. The adaptive testing engine was introduced to calculate student strength and weakness profiles dynamically.
*   *Learning Roadmaps*: Learners needed structured, chronological paths rather than static topic lists. Prerequisite traversal rules were added to build custom roadmaps.

---

## 3. Version 2: Multi-Tenant Enterprise SaaS

```text
Next.js Client ──> Nginx Proxy Gateway ──> FastAPI (RLS Session context active)
                                              ├── Celery Workers (Broker: Redis)
                                              ├── Redis Cache (Cache Service)
                                              └── PostgreSQL (Row-Level Security active)
```

### Architectural Profile
*   **Isolation**: Implemented multi-tenancy. Tables containing a `tenant_id` column were protected using PostgreSQL Row-Level Security (RLS) policies ([postgres_tenant_rls.sql](file:///home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls.sql)).
*   **Caches & Queues**: Added Redis cache engines and Celery background workers ([celery_app.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/celery_app.py)) to process long-running jobs.
*   **Proxy Edge**: Placed Nginx at the edge to handle client rate limiting and load balancing.
*   **Observability**: Integrated Prometheus exporters and Grafana dashboards to monitor system health.

### Why Features Were Introduced
*   *Postgres RLS Multi-Tenancy*: Required to sell the platform to enterprise customers (schools, corporations). Database-level RLS ensures strict data boundaries and prevents data leaks.
*   *Celery Workers*: Calculating diagnostic scores and generating roadmaps during HTTP requests caused API timeouts. Moving these tasks to background queues kept the user interface responsive.
*   *Redis Cache*: High-frequency queries (like loading topic graphs) placed heavy load on the database. Caching these reads in Redis improved page load speeds.

---

## 4. Current Architecture: Intelligent & Reliable SaaS

```text
Next.js Client ──> Nginx Gateway ──> FastAPI Monolith
                                         ├── outbox_events ──> Celery outbox Sweep
                                         └── AI Microservice (Multi-Agent Routing)
```

### Architectural Profile
*   **AI Decoupling**: Isolated the AI engine inside a separate FastAPI microservice ([ai_service/service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py)) to prevent LLM network latencies from locking core backend resources.
*   **Agent Orchestration**: Implemented a multi-agent supervisor system, dynamic digital twin simulations, and autonomous agent loops.
*   **Reliable Events**: Implemented the Transactional Event Outbox Pattern ([outbox_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/outbox_service.py)) to keep databases, caches, and queues in sync.

### Why Features Were Introduced
*   *Decoupled AI*: LLM API timeouts locked threads on the primary API. Decoupling the AI service protected core transactions.
*   *Digital Twin*: Introducing twin projections allowed the platform to simulate different learning strategies, helping students choose the most efficient path.
*   *Outbox Pattern*: Network failures between database transactions and cache updates caused data inconsistencies. Writing events to an outbox table atomically resolved this sync issue.

---

## 5. Development Timeline

```text
========================================================================
[DEVELOPMENT TIMELINE]
------------------------------------------------------------------------
Month 1-2   ──> Phase 1: Proof of Concept (FastAPI + SPA)
Month 3-5   ──> Phase 2: Layered Monolith & Adaptive Diagnostics
Month 6-8   ──> Phase 3: SaaS RLS Multi-Tenancy, Caches, & Celery
Month 9-11  ──> Phase 4: Decoupled AI Service & Multi-Agent Routing
Month 12+   ──> Phase 5: Transactional Outbox Pattern & K8s Deployments
========================================================================
```
