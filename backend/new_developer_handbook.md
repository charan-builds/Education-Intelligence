# New Developer Handbook

Welcome to the team! This handbook is designed to get you set up, oriented, and shipping code during your first week.

---

## 1. Repository Tour

```text
intelligentSystems/
├── backend/                    # Core FastAPI backend, DB logic, and tests
│   ├── alembic/                # Database migrations
│   ├── app/
│   │   ├── application/        # Application services and transactional workflows
│   │   ├── core/               # Configurations, security dependencies, and metrics
│   │   ├── domain/             # Core engines and database ORM models
│   │   ├── infrastructure/     # Database repositories and client adapters
│   │   └── presentation/       # API routers and middlewares
│   └── tests/                  # Backend test suite
├── learning-platform-frontend/ # Next.js frontend, components, and views
│   ├── app/                    # Next.js App Router folders and role layouts
│   ├── components/             # Reusable UI widgets and layout modules
│   └── tests/                  # Frontend unit and Playwright E2E tests
├── ai_service/                 # AI microservice for LLM agent routing
├── docs/                       # System architecture, deployment, and runbooks
├── k8s/                        # Production Kubernetes deployment manifests
└── nginx/                      # Edge routing gateway configurations
```

---

## 2. Local Development Setup

To build the application locally, run these commands in sequence:

### Step 1: Clone & Setup Environments
Confirm that Docker is active, then run:
```bash
make up
```
This builds and starts the PostgreSQL database, Redis caching nodes, Celery workers, and the Next.js frontend in the background.

### Step 2: Initialize Database Schemas
Run migrations and populate seed data:
```bash
make migrate
```

### Step 3: Run the Test Suite
Confirm that the installation is complete by running the backend test suite:
```bash
make test-backend
```

---

## 3. Coding Conventions

1.  **Strict Layer Separation**: API routes must not query the database directly. Always execute queries through repositories, and keep transaction coordination within service classes.
2.  **Linting & Style Guidelines**: Code formatting is enforced using Black and Ruff. Always run linting tools before committing code:
    ```bash
    ruff check . --fix
    black .
    ```
3.  **Strict Type Safety**: Declare explicit parameter types for all Python methods and use TypeScript interfaces for frontend API payloads.

---

## 4. Common Mistakes to Avoid

*   **Forgetting to enable RLS**: When creating new database tables containing a `tenant_id` column, always enable PostgreSQL RLS policies in SQL migration scripts.
*   **Importing repositories inside domains**: Keep domain engine classes pure and database-agnostic. Inject repository operations from the application layer.
*   **Leaking Secrets in Code**: Never commit credentials, tokens, or private keys to the git repository. Always load parameters from environment variables.

---

## 5. First-Week Plan

### Day 1: Build Local Environment
*   Follow the setup guide to build and run all local containers.
*   Log in to the local student dashboard at `http://localhost:3000`.

### Day 2: Run the Test Suite
*   Run backend pytests and verify they complete successfully.
*   Verify frontend component tests using Vitest.

### Day 3: Minor Task Fix
*   Locate an open feature flag ticket and submit a patch to update configurations.

### Day 4: Core Domain Walkthrough
*   Trace the diagnostic submission request flow from the router down to the adaptive testing engine.

### Day 5: Code Review & Sync
*   Submit a Pull Request for your fix and sync with the platform architect.
