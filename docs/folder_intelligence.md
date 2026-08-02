# Folder Intelligence Document

This document provides a detailed breakdown of every directory in the **Learning Intelligence Platform** repository. It serves as a comprehensive reference guide to help developers navigate the codebase, understand component ownership, trace data flow, and master the integration paths.

---

## Workspace Root Directories

### 1. `backend/`
*   **Purpose**: Houses the entire FastAPI application, database schema migrations, testing suites, runtime commands, and utility shell scripts.
*   **Owner**: Backend Platform Team.
*   **Dependencies**: PostgreSQL, Redis, Celery, and external pip dependencies defined in `pyproject.toml`.
*   **Files**: Contains Python source modules, shell startup files, dependency definitions, and Alembic database migration environments.
*   **Responsibilities**:
    *   Exposing the HTTP REST and WebSocket API.
    *   Running background jobs and schedulers.
    *   Accessing database tables and caching data.
    *   Evaluating diagnostic metrics and generating personalized roadmaps.
*   **Communication**: Routes public traffic through the Nginx gateway and communicates with the frontend via HTTP REST endpoints and WebSocket protocols.
*   **Critical Files**:
    *   [pyproject.toml](file:///home/charan_derangula/projects/intelligentSystems/backend/pyproject.toml) — Manages python packaging and environment dependencies.
    *   [run_workers.sh](file:///home/charan_derangula/projects/intelligentSystems/run_workers.sh) — Starts the background Celery queue worker processes.
*   **Important Entry Points**:
    *   [app/main.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/main.py) — The initialization point for the FastAPI server.
*   **Suggested Reading Order**:
    1.  [README.md](file:///home/charan_derangula/projects/intelligentSystems/backend/README.md)
    2.  [app/main.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/main.py)
    3.  [pyproject.toml](file:///home/charan_derangula/projects/intelligentSystems/backend/pyproject.toml)

---

### 2. `backend/alembic/`
*   **Purpose**: Manages the version history of the PostgreSQL database schema through SQLAlchemy-based migrations.
*   **Owner**: Database Administrator / Backend Platform Team.
*   **Dependencies**: [backend/app/domain/models/](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/models/) for entity mappings, and Alembic tooling.
*   **Files**: Contains auto-generated migration versions (under `versions/`), configuration files, and script templates.
*   **Responsibilities**:
    *   Running sequential database upgrades and rollbacks.
    *   Syncing database structures with local developer environments.
    *   Storing migration audit trails in the `alembic_version` table.
*   **Communication**: Modifies PostgreSQL tables directly using SQLAlchemy engines.
*   **Critical Files**:
    *   [env.py](file:///home/charan_derangula/projects/intelligentSystems/backend/alembic/env.py) — Initializes SQLAlchemy contexts and migration engines.
*   **Important Entry Points**:
    *   Execution starts when the CLI command `alembic upgrade head` is invoked.
*   **Suggested Reading Order**:
    1.  [env.py](file:///home/charan_derangula/projects/intelligentSystems/backend/alembic/env.py)
    2.  Inspect the latest Python files inside `versions/` to understand historical updates.

---

### 3. `backend/app/application/`
*   **Purpose**: Implements the Application layer of the modular monolith. It coordinates transactional use-cases and coordinates interactions between domain models and external service adapters.
*   **Owner**: Backend Feature Developers.
*   **Dependencies**: [backend/app/domain/](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/) for engines, and [backend/app/infrastructure/](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/) for data repositories.
*   **Files**: Core application service classes and cross-domain exceptions.
*   **Responsibilities**:
    *   Executing use-case actions (e.g. authenticating users, managing quiz questions, generating roadmap paths).
    *   Managing database transaction boundaries and saving changes.
    *   Triggering notifications and dispatching asynchronous worker tasks.
*   **Communication**: Triggered by presentation routers in `presentation/` and calls repositories/clients in `infrastructure/`.
*   **Critical Files**:
    *   [auth_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/auth_service.py) — Handles login, token authentication, and role assignments.
    *   [roadmap_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/roadmap_service.py) — Coordinates roadmap progression and goal management logic.
*   **Important Entry Points**:
    *   Service class public methods (e.g., `AuthService.login_user`).
*   **Suggested Reading Order**:
    1.  [auth_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/auth_service.py)
    2.  [roadmap_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/roadmap_service.py)
    3.  [exceptions.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/exceptions.py)

---

### 4. `backend/app/core/`
*   **Purpose**: Contains cross-cutting helpers, configuration classes, authentication primitives, metrics logging, and security middleware.
*   **Owner**: Security Team / Platform Leads.
*   **Dependencies**: Standard Python libraries, FastAPI security tools, Pydantic settings.
*   **Files**: Application configs, feature flag managers, log formatters, and Prometheus metrics setups.
*   **Responsibilities**:
    *   Loading environment variables from `.env` files.
    *   Validating API tokens and decrypting JWT keys.
    *   Logging structured JSON outputs for ELK/Promtail collectors.
    *   Exposing operational metrics for Prometheus scraping.
*   **Communication**: Loaded dynamically as FastAPI startup dependencies by almost every other backend folder.
*   **Critical Files**:
    *   [config.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/config.py) — Loads and validates config variables.
    *   [security.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/security.py) — Cryptographic helper tools (hashing, signing, validation).
*   **Important Entry Points**:
    *   [dependencies.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/dependencies.py) — Resolves database sessions and active user roles.
*   **Suggested Reading Order**:
    1.  [config.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/config.py)
    2.  [security.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/security.py)
    3.  [dependencies.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/dependencies.py)

---

### 5. `backend/app/domain/`
*   **Purpose**: The Domain Layer containing application engines, business calculation rules, graph logic, and SQLAlchemy ORM schemas.
*   **Owner**: Backend Domain Architects.
*   **Dependencies**: Relies only on standard python libraries and declarative schemas. It is decoupled from presentation and infrastructure adapters.
*   **Files**: Python ORM classes, adaptive diagnostic models, and knowledge graph traversal routines.
*   **Responsibilities**:
    *   Defining the core database entities (e.g. `User`, `Roadmap`, `Tenant`).
    *   Calculating student strength/weakness vectors and quiz accuracy profiles.
    *   Tracing skill trees and resolving prerequisite graphs.
*   **Communication**: Invoked by application service classes. Domain classes are database-agnostic and operate entirely in-memory.
*   **Critical Files**:
    *   [knowledge_graph.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/knowledge_graph.py) — Traverses skill connections and prereqs.
    *   [adaptive_testing_engine.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/adaptive_testing_engine.py) — Chooses next quiz questions based on response histories.
*   **Important Entry Points**:
    *   Engine calculation methods (e.g., `AdaptiveTestingEngine.get_next_question`).
*   **Suggested Reading Order**:
    1.  [models/user.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/models/user.py) to inspect core entity structures.
    2.  [engines/adaptive_testing_engine.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/adaptive_testing_engine.py)
    3.  [engines/knowledge_graph.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/knowledge_graph.py)

---

### 6. `backend/app/events/`
*   **Purpose**: Manages event wrappers, schemas, and topics used to distribute events to messaging channels.
*   **Owner**: Backend Integration Team.
*   **Dependencies**: Pydantic validation frameworks.
*   **Files**: Event schemas, topic lists, and schema registry logic.
*   **Responsibilities**:
    *   Structuring outbox events to prevent format mismatches.
    *   Defining available Kafka/Redis stream channels.
    *   Serializing and deserializing network data payloads.
*   **Communication**: Application services write events to these schemas, and infrastructure dispatchers publish them.
*   **Critical Files**:
    *   [event_envelope.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/events/event_envelope.py) — Defines wrappers containing transaction and source metadata.
*   **Important Entry Points**:
    *   Schemas are instantiated by application services before dispatch.
*   **Suggested Reading Order**:
    1.  [event_envelope.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/events/event_envelope.py)
    2.  [kafka_topics.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/events/kafka_topics.py)

---

### 7. `backend/app/infrastructure/`
*   **Purpose**: Contains technical adapters, SQL repository files, Redis clients, Celery jobs, and API client wrappers.
*   **Owner**: SRE / Infrastructure Engineering.
*   **Dependencies**: [backend/app/domain/](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/) for repository implementations, and external drivers (SQLAlchemy, Redis, Celery).
*   **Files**: Data repositories, Celery configuration settings, Redis caches, and AI service clients.
*   **Responsibilities**:
    *   Writing and reading data via database repository queries.
    *   Processing cached keys in Redis.
    *   Executing asynchronous Celery jobs.
    *   Handling HTTP calls to the AI Service.
*   **Communication**: Implements interfaces defined by higher layers. Services in `application/` invoke repositories to query data.
*   **Critical Files**:
    *   [database.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/database.py) — Connects to Postgres and provisions sessions.
    *   [celery_app.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/celery_app.py) — Configures Celery jobs and broker task lists.
    *   [tenant_rls.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/tenant_rls.py) — Attaches tenant contexts to PostgreSQL connections.
*   **Important Entry Points**:
    *   [jobs/tasks.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/jobs/tasks.py) — Entry point for all Celery worker processes.
*   **Suggested Reading Order**:
    1.  [database.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/database.py)
    2.  [tenant_rls.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/tenant_rls.py)
    3.  [repositories/user_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
    4.  [celery_app.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/celery_app.py)

---

### 8. `backend/app/presentation/`
*   **Purpose**: The Presentation Layer containing HTTP endpoints, routing managers, custom middleware, and exception handlers.
*   **Owner**: Backend API Developers.
*   **Dependencies**: [backend/app/application/](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/) use-cases, and [backend/app/schemas/](file:///home/charan_derangula/projects/intelligentSystems/backend/app/schemas/) validation modules.
*   **Files**: Route modules, rate-limiting middleware, logging handlers.
*   **Responsibilities**:
    *   Defining the API routes (e.g. `/auth/login`, `/roadmap/generate`).
    *   Parsing and validating request body schemas.
    *   Formatting REST response values.
    *   Translating runtime exceptions into clean HTTP status errors.
*   **Communication**: Invoked by clients via Nginx and routes requests to service modules in `application/`.
*   **Critical Files**:
    *   [api_router.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/presentation/api_router.py) — Integrates all sub-routers.
    *   [middleware/rate_limiter.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/presentation/middleware/rate_limiter.py) — Mitigates request bursts.
*   **Important Entry Points**:
    *   FastAPI route decorators (`@router.post(...)`).
*   **Suggested Reading Order**:
    1.  [api_router.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/presentation/api_router.py)
    2.  [auth_routes.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/presentation/auth_routes.py)
    3.  [middleware/rate_limiter.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/presentation/middleware/rate_limiter.py)

---

### 9. `backend/app/realtime/`
*   **Purpose**: Manages real-time communications over persistent WebSocket connections.
*   **Owner**: Backend Collaboration Team.
*   **Dependencies**: FastAPI WebSockets, Redis message buses.
*   **Files**: Connection managers, WebSocket hub logic, and messaging buses.
*   **Responsibilities**:
    *   Tracking active WebSocket connection states.
    *   Routing events across server clusters using Redis.
    *   Broadcasting notifications and chat messages instantly.
*   **Communication**: Coordinates data flow between backend services and active browser sockets.
*   **Critical Files**:
    *   [hub.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/realtime/hub.py) — Manages subscriber lists.
    *   [distributed_bus.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/realtime/distributed_bus.py) — Links separate instances using Redis Pub/Sub channels.
*   **Important Entry Points**:
    *   [realtime_routes.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/presentation/realtime_routes.py) — The target WebSocket connection endpoint.
*   **Suggested Reading Order**:
    1.  [hub.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/realtime/hub.py)
    2.  [distributed_bus.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/realtime/distributed_bus.py)

---

### 10. `backend/app/schemas/`
*   **Purpose**: Contains Pydantic serialization models used to validate request bodies and format API JSON outputs.
*   **Owner**: Backend API Developers.
*   **Dependencies**: Pydantic validation library.
*   **Files**: API schemas for schemas modules.
*   **Responsibilities**:
    *   Enforcing property formats (e.g. verifying email formats, validating UUIDs).
    *   Preventing unexpected fields from entering application logic.
    *   Structuring JSON outputs for API clients.
*   **Communication**: Imported by routers in `presentation/` and services in `application/`.
*   **Critical Files**:
    *   [auth_schema.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/schemas/auth_schema.py) — Validates credential request formats.
    *   [roadmap_schema.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/schemas/roadmap_schema.py) — Validates roadmap metadata responses.
*   **Important Entry Points**:
    *   Schemas are instantiated by route handlers during request validation.
*   **Suggested Reading Order**:
    1.  [auth_schema.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/schemas/auth_schema.py)
    2.  [roadmap_schema.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/schemas/roadmap_schema.py)

---

### 11. `backend/scripts/`
*   **Purpose**: Contains operational tooling, chaos testing scenarios, and performance profiling scripts.
*   **Owner**: SRE / DevOps Team.
*   **Dependencies**: Python test runner modules, API endpoints.
*   **Files**: Chaos trigger files, seed data tools, performance smoke tests.
*   **Responsibilities**:
    *   Injecting seed data during deployment setups.
    *   Running stress test scripts to profile API scaling limits.
    *   Injecting errors to test retry recovery flows.
*   **Communication**: Invokes API endpoints over standard HTTP networks.
*   **Critical Files**:
    *   [start_api.sh](file:///home/charan_derangula/projects/intelligentSystems/backend/scripts/ops/start_api.sh) — Runs migrations and starts the FastAPI runtime.
*   **Important Entry Points**:
    *   Triggered manually by developers or automatically inside CI/CD pipelines.
*   **Suggested Reading Order**:
    1.  [ops/start_api.sh](file:///home/charan_derangula/projects/intelligentSystems/backend/scripts/ops/start_api.sh)
    2.  Explore the test scripts inside `load/` and `chaos/` to understand chaos testing logic.

---

### 12. `backend/sql/`
*   **Purpose**: Contains raw SQL scripts, tenant setup logic, and database trigger definitions.
*   **Owner**: Database Administrator / Security Team.
*   **Dependencies**: Direct PostgreSQL contexts.
*   **Files**: PostgreSQL procedural SQL modules.
*   **Responsibilities**:
    *   Enabling Row-Level Security configurations.
    *   Provisions database triggers to update timestamps.
    *   Setting up isolated tenant schema boundaries.
*   **Communication**: Loaded during migration runs or applied manually via SQL clients.
*   **Critical Files**:
    *   [postgres_tenant_rls.sql](file:///home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls.sql) — Configures Postgres RLS database rules.
*   **Important Entry Points**:
    *   Scripts run during database initialization or database updates.
*   **Suggested Reading Order**:
    1.  [postgres_tenant_rls.sql](file:///home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls.sql)

---

### 13. `backend/tests/`
*   **Purpose**: The Backend test suite containing unit, integration, and security tests.
*   **Owner**: Backend Platform Quality Team.
*   **Dependencies**: `pytest`, `pytest-asyncio`, and target source modules.
*   **Files**: Test scripts, mock resources, test configurations (`conftest.py`).
*   **Responsibilities**:
    *   Validating database CRUD logic.
    *   Verifying that RLS policies block cross-tenant queries.
    *   Testing Celery outbox retry flows.
*   **Communication**: Invokes application services and mocks database tables inside testing namespaces.
*   **Critical Files**:
    *   [conftest.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/conftest.py) — Configures async test databases and scopes mocks.
*   **Important Entry Points**:
    *   Invoked by executing the CLI command `pytest`.
*   **Suggested Reading Order**:
    1.  [conftest.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/conftest.py)
    2.  [integration/test_auth.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_auth.py)
    3.  [unit/test_tenant_isolation.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/unit/test_tenant_isolation.py)

---

## Frontend Directories

### 14. `learning-platform-frontend/app/`
*   **Purpose**: The Next.js 15 App Router directory containing pages, layouts, and role-based panels.
*   **Owner**: Frontend Engineering UI Team.
*   **Dependencies**: React, Next.js framework libraries, and services in `services/`.
*   **Files**: Page controllers (`page.tsx`), root shell layouts (`layout.tsx`), error boundaries.
*   **Responsibilities**:
    *   Managing page routing and view rendering.
    *   Guarding panels based on user roles (`(student)`, `(teacher)`, `(admin)`).
    *   Interpreting URL query parameters to load active tenant scopes.
*   **Communication**: Fetches data from backend APIs via HTTP, and renders pages based on state changes.
*   **Critical Files**:
    *   [layout.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/app/layout.tsx) — Provisions state providers (QueryClient, Auth).
    *   [middleware.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/middleware.ts) — Validates route access before rendering.
*   **Important Entry Points**:
    *   [page.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/app/page.tsx) — Main entry point for landing traffic.
*   **Suggested Reading Order**:
    1.  [middleware.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/middleware.ts)
    2.  [layout.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/app/layout.tsx)
    3.  [page.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/app/page.tsx)

---

### 15. `learning-platform-frontend/components/`
*   **Purpose**: Houses modular, reusable React UI components.
*   **Owner**: Frontend UX / Design Team.
*   **Dependencies**: React, Tailwind class composition helpers (`cn.ts`).
*   **Files**: Button states, form structures, sidebars, dashboard charts.
*   **Responsibilities**:
    *   Rendering consistent, styled UI components.
    *   Binding UI elements to interactive event listeners.
    *   Adapting views to match mobile and desktop screen widths.
*   **Communication**: Receives data and action triggers from page components via React props.
*   **Critical Files**:
    *   [ui/button.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/ui/button.tsx) — Base reusable button styles.
*   **Important Entry Points**:
    *   Individual UI components imported inside pages.
*   **Suggested Reading Order**:
    1.  Review components inside `ui/` to inspect base style tokens.
    2.  Inspect dashboard components inside `dashboard/` to trace analytics bindings.

---

### 16. `learning-platform-frontend/features/`
*   **Purpose**: Houses domain-specific feature modules containing pages and components.
*   **Owner**: Frontend Feature Leads.
*   **Dependencies**: [learning-platform-frontend/components/](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/) UI components, and API service wrappers.
*   **Files**: Feature-specific UI files.
*   **Responsibilities**:
    *   Isolating domain-specific components (e.g. Diagnostic quiz flows, Roadmap editors).
    *   Grouping related logic to simplify future code separations.
*   **Communication**: Imported inside specific page layout containers.
*   **Critical Files**:
    *   [diagnostic/DiagnosticQuiz.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/features/diagnostic/DiagnosticQuiz.tsx) — Manages diagnostic quiz view states.
*   **Important Entry Points**:
    *   Main feature components (e.g., `DiagnosticQuiz`).
*   **Suggested Reading Order**:
    1.  [diagnostic/DiagnosticQuiz.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/features/diagnostic/DiagnosticQuiz.tsx)
    2.  [roadmap/RoadmapViewer.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/features/roadmap/RoadmapViewer.tsx)

---

### 17. `learning-platform-frontend/hooks/`
*   **Purpose**: Custom React hooks for auth states, tenant resolution, and quiz countdowns.
*   **Owner**: Frontend Platform Team.
*   **Dependencies**: React, React Query client libraries, and browser APIs.
*   **Files**: Reusable custom react hooks.
*   **Responsibilities**:
    *   Encapsulating state logic (e.g., tracking session timeouts, counting down remaining quiz time).
    *   Resolving current tenant names from URL subdomains.
*   **Communication**: Imported by visual components to access reactive state contexts.
*   **Critical Files**:
    *   [useAuth.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/hooks/useAuth.ts) — Wraps token states and role mappings.
    *   [useTenantScope.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/hooks/useTenantScope.ts) — Intercepts and parses URL subdomains.
*   **Important Entry Points**:
    *   Hook methods called inside page components.
*   **Suggested Reading Order**:
    1.  [useAuth.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/hooks/useAuth.ts)
    2.  [useTenantScope.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/hooks/useTenantScope.ts)

---

### 18. `learning-platform-frontend/lib/`
*   **Purpose**: Configures shared HTTP clients and external API integrations.
*   **Owner**: Frontend Platform Team.
*   **Dependencies**: Axios libraries, browser cookie managers.
*   **Files**: Axios instance configurations, header interception policies.
*   **Responsibilities**:
    *   Setting up Axios clients with fallback settings.
    *   Adding Bearer tokens to request headers.
    *   Intercepting network errors to coordinate token refreshes.
*   **Communication**: Invoked by files inside the services folder to query APIs.
*   **Critical Files**:
    *   [api.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/lib/api.ts) — Configures base Axios clients and interceptors.
*   **Important Entry Points**:
    *   Shared HTTP endpoints.
*   **Suggested Reading Order**:
    1.  [api.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/lib/api.ts)

---

### 19. `learning-platform-frontend/public/`
*   **Purpose**: Contains static assets like images, SVG vectors, and typography files.
*   **Owner**: Design Team / Frontend developers.
*   **Dependencies**: Served directly by Nginx or Next.js web servers.
*   **Files**: PNG/SVG graphics and CSS styling files.
*   **Responsibilities**:
    *   Storing branding files and illustration vectors.
    *   Serving favicon files.
*   **Communication**: Read directly by browser requests.
*   **Critical Files**:
    *   [favicon.ico](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/public/favicon.ico)
*   **Suggested Reading Order**:
    1.  Visual review of static branding assets under `assets/`.

---

### 20. `learning-platform-frontend/services/`
*   **Purpose**: The data fetching service layer containing typed API client wrappers.
*   **Owner**: Frontend Platform Team.
*   **Dependencies**: [learning-platform-frontend/lib/api.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/lib/api.ts) clients.
*   **Files**: Client wrappers.
*   **Responsibilities**:
    *   Declaring request/response types for API calls.
    *   Encapsulating route paths (e.g. `/api/auth/login`).
    *   Handling API failures gracefully.
*   **Communication**: Imported inside React Query structures to fetch data.
*   **Critical Files**:
    *   [apiClient.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/services/apiClient.ts) — Extends base Axios client setups.
    *   [authService.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/services/authService.ts) — Executes authentication API calls.
*   **Important Entry Points**:
    *   Client service methods (e.g., `authService.login`).
*   **Suggested Reading Order**:
    1.  [apiClient.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/services/apiClient.ts)
    2.  [authService.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/services/authService.ts)

---

### 21. `learning-platform-frontend/store/` & `learning-platform-frontend/stores/`
*   **Purpose**: Manages global client-side state using Zustand.
*   **Owner**: Frontend UI Architecture Team.
*   **Dependencies**: Zustand libraries.
*   **Files**: Zustand reactive store schemas.
*   **Responsibilities**:
    *   Storing client-side UI state (e.g., selected menu tabs, countdown values).
    *   Providing action methods to update global states.
*   **Communication**: Invoked by page elements to read and write state properties.
*   **Critical Files**:
    *   [useDiagnosticTestStore.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/stores/useDiagnosticTestStore.ts) — Tracks ongoing diagnostic quiz responses.
*   **Important Entry Points**:
    *   Store hooks used in client views.
*   **Suggested Reading Order**:
    1.  [useDiagnosticTestStore.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/stores/useDiagnosticTestStore.ts)

---

### 22. `learning-platform-frontend/tests/`
*   **Purpose**: Contains frontend test suites, including Vitest unit tests and Playwright E2E scenarios.
*   **Owner**: Quality Assurance / Frontend Leads.
*   **Dependencies**: Playwright, Vitest test runners, and target frontend components.
*   **Files**: Playwright test files (`*.spec.ts`), mock configurations.
*   **Responsibilities**:
    *   Running browser integration flows (e.g. logging in, switching tenants).
    *   Verifying component rendering behaviors.
*   **Communication**: Launches automated browsers to simulate user actions against the frontend interface.
*   **Critical Files**:
    *   [e2e/learner-journey.spec.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/tests/e2e/learner-journey.spec.ts) — Asserts diagnostic quiz and roadmap viewer behaviors.
*   **Important Entry Points**:
    *   Invoked by executing the CLI commands `npx playwright test` or `vitest`.
*   **Suggested Reading Order**:
    1.  [e2e/live-login.spec.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/tests/e2e/live-login.spec.ts)
    2.  [e2e/learner-journey.spec.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/tests/e2e/learner-journey.spec.ts)

---

### 23. `learning-platform-frontend/types/`
*   **Purpose**: Defines TypeScript type schemas that mirror backend API schemas.
*   **Owner**: Frontend Platform Team.
*   **Dependencies**: None.
*   **Files**: TypeScript interface and type declaration files.
*   **Responsibilities**:
    *   Declaring static property structures.
    *   Verifying API data bindings during compile-time checks.
*   **Communication**: Imported globally by UI components and API clients.
*   **Critical Files**:
    *   [auth.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/types/auth.ts) — Defines user, role, and token interfaces.
*   **Suggested Reading Order**:
    1.  [auth.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/types/auth.ts)
    2.  [diagnostic.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/types/diagnostic.ts)

---

### 24. `learning-platform-frontend/utils/`
*   **Purpose**: Reusable pure helper functions for string formatting, CSS tailwind merging, and route redirections.
*   **Owner**: Frontend Platform Team.
*   **Dependencies**: CSS class-merging utility dependencies.
*   **Files**: CSS merge utilities, token parsing helpers.
*   **Responsibilities**:
    *   Merging Tailwind CSS utility classes dynamically.
    *   Handling cookie strings.
    *   Determining role-based route redirects.
*   **Communication**: Imported inside component files.
*   **Critical Files**:
    *   [cn.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/utils/cn.ts) — Tailwind merge utility helper.
    *   [roleRedirect.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/utils/roleRedirect.ts) — Resolves target dashboards after login.
*   **Suggested Reading Order**:
    1.  [roleRedirect.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/utils/roleRedirect.ts)
    2.  [cn.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/utils/cn.ts)

---

## AI Subsystem

### 25. `ai_service/`
*   **Purpose**: Exposes AI prompt orchestration tools, specialist agents, and guardrails via a separate FastAPI service.
*   **Owner**: AI/ML Platform Team.
*   **Dependencies**: OpenAI/Gemini SDKs, standard Python frameworks.
*   **Files**: FastAPI service app, client libraries, system prompts, schemas, guardrails.
*   **Responsibilities**:
    *   Structuring LLM prompt contexts.
    *   Routing messages across agent pools.
    *   Applying guardrail filters to screen input queries and output responses.
*   **Communication**: Invoked by the primary backend via HTTP client requests over port 8100.
*   **Critical Files**:
    *   [main.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/main.py) — Exposes AI REST API routes.
    *   [service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py) — Manages supervisor agent routing.
    *   [prompts.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/prompts.py) — System instructions for agents.
*   **Important Entry Points**:
    *   `/ai/mentor-chat` API endpoint.
*   **Suggested Reading Order**:
    1.  [main.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/main.py)
    2.  [service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py)
    3.  [prompts.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/prompts.py)

---

## Infrastructure, Gateway & Configs

### 26. `docs/`
*   **Purpose**: Central documentation repository containing system architecture diagrams, launch checklists, and runbooks.
*   **Owner**: Architecture Committee / Tech Leads.
*   **Dependencies**: None.
*   **Files**: Markdown documentation files.
*   **Responsibilities**:
    *   Explaining architectural designs to developers.
    *   Documenting incident response runbooks.
*   **Critical Files**:
    *   [learning_intelligence_platform_architecture.md](file:///home/charan_derangula/projects/intelligentSystems/docs/learning_intelligence_platform_architecture.md) — The system architecture document.
*   **Suggested Reading Order**:
    1.  [learning_intelligence_platform_architecture.md](file:///home/charan_derangula/projects/intelligentSystems/docs/learning_intelligence_platform_architecture.md)
    2.  [production-deployment.md](file:///home/charan_derangula/projects/intelligentSystems/docs/production-deployment.md)

---

### 27. `k8s/`
*   **Purpose**: Houses Kubernetes manifests to deploy stateful and stateless components to production clusters.
*   **Owner**: SRE / DevOps Team.
*   **Dependencies**: Kubernetes cluster runtime environments.
*   **Files**: YAML config manifests.
*   **Responsibilities**:
    *   Configuring pod replications and deployment counts.
    *   Defining ingress routing and network firewall policies.
    *   Configuring Horizontal Pod Autoscaler (HPA) triggers.
*   **Communication**: Applied to cluster controllers to provision infrastructure resources.
*   **Critical Files**:
    *   [api.yaml](file:///home/charan_derangula/projects/intelligentSystems/k8s/api.yaml) — Deployment spec for FastAPI containers.
    *   [ingress.yaml](file:///home/charan_derangula/projects/intelligentSystems/k8s/ingress.yaml) — Handles cluster route mappings.
*   **Suggested Reading Order**:
    1.  [namespace.yaml](file:///home/charan_derangula/projects/intelligentSystems/k8s/namespace.yaml)
    2.  [api.yaml](file:///home/charan_derangula/projects/intelligentSystems/k8s/api.yaml)
    3.  [ingress.yaml](file:///home/charan_derangula/projects/intelligentSystems/k8s/ingress.yaml)

---

### 28. `monitoring/`
*   **Purpose**: Observability configurations, including Prometheus rules, Grafana provisioning setups, and Alertmanager routers.
*   **Owner**: SRE / Operations Team.
*   **Dependencies**: Prometheus, Grafana, Alertmanager docker runtimes.
*   **Files**: Prometheus YAML rules, Grafana JSON dashboards.
*   **Responsibilities**:
    *   Configuring metric scraping intervals.
    *   Defining operational alert conditions (e.g. high CPU load, high latency, queue backlogs).
    *   Pre-provisioning dashboards for real-time traffic inspections.
*   **Communication**: Scrapes metric endpoints from API containers.
*   **Critical Files**:
    *   [prometheus/prometheus.yml](file:///home/charan_derangula/projects/intelligentSystems/monitoring/prometheus/prometheus.yml) — Targets endpoint metrics.
    *   [prometheus/alerts.yml](file:///home/charan_derangula/projects/intelligentSystems/monitoring/prometheus/alerts.yml) — Evaluates alert expressions.
*   **Suggested Reading Order**:
    1.  [prometheus/prometheus.yml](file:///home/charan_derangula/projects/intelligentSystems/monitoring/prometheus/prometheus.yml)
    2.  [prometheus/alerts.yml](file:///home/charan_derangula/projects/intelligentSystems/monitoring/prometheus/alerts.yml)

---

### 29. `nginx/`
*   **Purpose**: Exposes Nginx proxy configurations to handle edge routing, TLS certificates, and rate limiting.
*   **Owner**: SRE Team.
*   **Dependencies**: Nginx web server.
*   **Files**: Nginx text configuration files.
*   **Responsibilities**:
    *   Forwarding client traffic to backend containers.
    *   Buffering requests and responses.
    *   Blocking client IPs during request bursts.
*   **Communication**: Proxies incoming internet traffic to backend services.
*   **Critical Files**:
    *   [nginx.conf](file:///home/charan_derangula/projects/intelligentSystems/nginx/nginx.conf) — Main server settings and buffers.
    *   [frontend_gateway.conf](file:///home/charan_derangula/projects/intelligentSystems/nginx/frontend_gateway.conf) — Configures route proxies.
*   **Suggested Reading Order**:
    1.  [nginx.conf](file:///home/charan_derangula/projects/intelligentSystems/nginx/nginx.conf)
    2.  [frontend_gateway.conf](file:///home/charan_derangula/projects/intelligentSystems/nginx/frontend_gateway.conf)
