# Learning Curriculum

This curriculum contains 60 sequential lessons designed to guide developers from onboarding up to primary maintainer level.

---

## Curriculum Structure

```text
========================================================================
[CURRICULUM PHASES]
------------------------------------------------------------------------
Phase 1  ──> Lessons 01-06: Local Environment & Testing Primitives
Phase 2  ──> Lessons 07-12: Multi-Tenancy & Row-Level Security (RLS)
Phase 3  ──> Lessons 13-18: Authentication, Encryption, & JWT
Phase 4  ──> Lessons 19-24: Prerequisite Graphs & Topological sorting
Phase 5  ──> Lessons 25-30: Adaptive Testing Engine
Phase 6  ──> Lessons 31-36: Real-time WebSockets & Redis Pub/Sub
Phase 7  ──> Lessons 37-42: AI microservice & Agent Routing
Phase 8  ──> Lessons 43-48: Transactional Outbox Sweeps & Celery
Phase 9  ──> Lessons 49-54: Observability, Metrics, & Alarms
Phase 10 ──> Lessons 55-60: Kubernetes, Scaling, & Redesign
========================================================================
```

---

## Phase 1: Local Environment & Testing Primitives (Lessons 1-6)

### Lesson 01: Setup & Local Container Topology
*   **Topic**: Container architecture.
*   **Objectives**: Spin up local containers and verify routing paths.
*   **Files to Study**: [docker-compose.yml](file:///home/charan_derangula/projects/intelligentSystems/docker-compose.yml) and [Makefile](file:///home/charan_derangula/projects/intelligentSystems/Makefile).
*   **APIs**: `GET /health`.
*   **Database**: None.
*   **Hands-on Exercise**: Add a new environment variable to the API container and verify it inside the health route.
*   **Debugging Task**: Force Nginx to return a 502 error and check the logs.
*   **Interview Question**: Why use Nginx in local development instead of connecting directly to the API?
*   **Quiz**: What port does the local proxy gateway expose? (Answer: Port 8000).

### Lesson 02: Running Pytest and Mocking Database Calls
*   **Topic**: Backend unit tests.
*   **Objectives**: Execute tests and mock database sessions.
*   **Files to Study**: [conftest.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/conftest.py).
*   **APIs**: None.
*   **Database**: Mock database connections.
*   **Hands-on Exercise**: Write a unit test that mocks database sessions to verify user creation.
*   **Debugging Task**: Fix a failing test caused by an uncommitted transaction.
*   **Interview Question**: Why should unit tests verify code logic in-memory without making actual database queries?
*   **Quiz**: What decorator is used to mock asynchronous functions? (Answer: `unittest.mock.patch`).

### Lesson 03: Playwright E2E Integration Checks
*   **Topic**: Headless browser automation.
*   **Objectives**: Run E2E test suites.
*   **Files to Study**: [learner-journey.spec.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/tests/e2e/learner-journey.spec.ts).
*   **APIs**: API authentication endpoints.
*   **Database**: `users`.
*   **Hands-on Exercise**: Add an assertion to the E2E script to verify the dashboard loads.
*   **Debugging Task**: Fix a failing E2E script caused by slow page loads.
*   **Interview Question**: When should you use unit tests vs. E2E browser tests?
*   **Quiz**: What command runs Playwright tests locally? (Answer: `npx playwright test`).

### Lesson 04: Vitest Frontend Unit Assertions
*   **Topic**: Frontend component testing.
*   **Objectives**: Write component tests using Vitest.
*   **Files to Study**: Frontend unit tests.
*   **APIs**: None.
*   **Database**: None.
*   **Hands-on Exercise**: Write a component test to verify that the countdown timer renders.
*   **Debugging Task**: Fix a component test failing due to missing state provider contexts.
*   **Interview Question**: How does Vitest speed up test runs compared to Jest?
*   **Quiz**: What library mock parses component renders? (Answer: React Testing Library).

### Lesson 05: Seed Data Provisioning
*   **Topic**: Database seeding.
*   **Objectives**: Populate seed records.
*   **Files to Study**: Database seed configurations.
*   **APIs**: None.
*   **Database**: `users`, `topics`, `questions`.
*   **Hands-on Exercise**: Add custom questions to seed files and migrate.
*   **Debugging Task**: Resolve database constraint failures during seeding.
*   **Interview Question**: Why should dev and test databases use consistent seed datasets?
*   **Quiz**: Which command applies database seed sets? (Answer: `make seed`).

### Lesson 06: CI/CD Pipeline Checks
*   **Topic**: GitHub Actions.
*   **Objectives**: Verify pipeline checks.
*   **Files to Study**: GitHub Actions workflow configurations.
*   **APIs**: None.
*   **Database**: None.
*   **Hands-on Exercise**: Add linting rules to the CI pipeline configurations.
*   **Debugging Task**: Resolve pipeline check failures caused by missing environment variables.
*   **Interview Question**: What is the difference between continuous integration (CI) and continuous delivery (CD)?
*   **Quiz**: Which tool enforces code formatting in the CI pipeline? (Answer: Ruff).

---

## Phase 2: Multi-Tenancy & Row-Level Security (Lessons 7-12)

### Lesson 07: Row-Level Security Fundamentals
*   **Topic**: Postgres RLS.
*   **Objectives**: Enable RLS policies on tables.
*   **Files to Study**: [postgres_tenant_rls.sql](file:///home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls.sql).
*   **APIs**: None.
*   **Database**: `goals`.
*   **Hands-on Exercise**: Enable RLS on the `goals` table.
*   **Debugging Task**: Fix a query returning empty results due to unset tenant context variables.
*   **Interview Question**: How does RLS protect tenant data?
*   **Quiz**: What command enables RLS on a table? (Answer: `ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;`).

### Lesson 08: Context Injection Middleware
*   **Topic**: Tenant middleware.
*   **Objectives**: Inject tenant context into queries.
*   **Files to Study**: [tenant_rls.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/tenant_rls.py).
*   **APIs**: Tenant lookup API.
*   **Database**: All tenant-scoped tables.
*   **Hands-on Exercise**: Write custom middleware to inject tenant context into requests.
*   **Debugging Task**: Fix a context leak issue where tenant context is not cleared between requests.
*   **Interview Question**: How do you prevent context leakage in connection pools?
*   **Quiz**: What session setting sets local variables? (Answer: `SET LOCAL`).

### Lesson 09: Tenant Index Optimization
*   **Topic**: DB performance tuning.
*   **Objectives**: Optimize tenant queries.
*   **Files to Study**: [postgres_index_recommendations.sql](file:///home/charan_derangula/projects/intelligentSystems/docs/postgres_index_recommendations.sql).
*   **APIs**: None.
*   **Database**: `learning_events`.
*   **Hands-on Exercise**: Create a composite index to optimize tenant queries.
*   **Debugging Task**: Fix slow tenant queries using database profiling tools.
*   **Interview Question**: Why should tenant ID columns be included in composite indexes?
*   **Quiz**: What statement displays query execution plans? (Answer: `EXPLAIN ANALYZE`).

### Lesson 10: RLS Audit & Compliance Validation
*   **Topic**: Security audits.
*   **Objectives**: Audit database tables for RLS compliance.
*   **Files to Study**: [tenant_rls_audit_20260402.md](file:///home/charan_derangula/projects/intelligentSystems/docs/tenant_rls_audit_20260402.md).
*   **APIs**: All endpoints.
*   **Database**: System tables (`pg_policy`).
*   **Hands-on Exercise**: Write a script to audit database tables for missing RLS policies.
*   **Debugging Task**: Fix missing RLS policies on audit log tables.
*   **Interview Question**: What are the risks of a mixed-mode RLS configuration?
*   **Quiz**: Which view catalog displays active RLS policies? (Answer: `pg_policies`).

### Lesson 11: Dynamic Tenant Subdomain Routing
*   **Topic**: Next.js middleware.
*   **Objectives**: Configure tenant subdomain routing.
*   **Files to Study**: [middleware.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/middleware.ts).
*   **APIs**: Tenant verification API.
*   **Database**: `tenants`.
*   **Hands-on Exercise**: Configure dynamic subdomain routing in Next.js middleware.
*   **Debugging Task**: Fix routing issues caused by missing subdomain mapping configurations.
*   **Interview Question**: How does subdomain-based routing improve tenant isolation?
*   **Quiz**: How does Next.js middleware inspect subdomains? (Answer: `request.nextUrl.hostname`).

### Lesson 12: Super Admin Override Controls
*   **Topic**: Admin override logic.
*   **Objectives**: Configure admin bypass capabilities.
*   **Files to Study**: [dependencies.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/dependencies.py).
*   **APIs**: All administrative APIs.
*   **Database**: `users`.
*   **Hands-on Exercise**: Implement an admin override check in authentication dependencies.
*   **Debugging Task**: Fix security checks allowing non-admin accounts to bypass RLS policies.
*   **Interview Question**: How do you secure administrative overrides in a multi-tenant application?
*   **Quiz**: What header overrides tenant boundaries? (Answer: `X-Tenant-ID`).

---

## Phase 3: Authentication, Encryption, & JWT (Lessons 13-18)

### Lesson 13: Password Hashing with Bcrypt
*   **Topic**: Password security.
*   **Objectives**: Hash credentials using Bcrypt.
*   **Files to Study**: [security.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/security.py) and [auth_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/auth_service.py).
*   **APIs**: `POST /auth/register` and `POST /auth/login`.
*   **Database**: `users`.
*   **Hands-on Exercise**: Update Bcrypt rounds parameters to adjust hashing computational costs.
*   **Debugging Task**: Debug connection timeouts caused by high hashing costs under load.
*   **Interview Question**: Why use Bcrypt instead of MD5 or SHA-256 for password hashing?
*   **Quiz**: What argument controls Bcrypt computational costs? (Answer: rounds).

### Lesson 14: Stateless JWT Access Keys
*   **Topic**: Token authentication.
*   **Objectives**: Generate and verify JWT access keys.
*   **Files to Study**: [security.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/security.py).
*   **APIs**: Authentication endpoints.
*   **Database**: None.
*   **Hands-on Exercise**: Add custom role claims to access token payloads.
*   **Debugging Task**: Debug expired signature exceptions in token validations.
*   **Interview Question**: What is the risk of using stateless JWT access keys?
*   **Quiz**: What algorithm signs JWT tokens? (Answer: HS256).

### Lesson 15: HttpOnly Cookie Refresh Tokens
*   **Topic**: Session security.
*   **Objectives**: Store refresh tokens securely in cookies.
*   **Files to Study**: [auth_routes.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/presentation/auth_routes.py).
*   **APIs**: `POST /auth/refresh`.
*   **Database**: `refresh_tokens`.
*   **Hands-on Exercise**: Configure secure, HttpOnly, and SameSite parameters on refresh cookies.
*   **Debugging Task**: Debug refresh token verification failures on client requests.
*   **Interview Question**: Why store refresh tokens in HttpOnly cookies instead of localStorage?
*   **Quiz**: Which parameter blocks Javascript token reads? (Answer: `httponly=True`).

### Lesson 16: JWT Revocation Blacklists in Redis
*   **Topic**: Session revocation.
*   **Objectives**: Revoke active tokens on logout.
*   **Files to Study**: Cache service configurations.
*   **APIs**: `POST /auth/logout`.
*   **Database**: Redis key store.
*   **Hands-on Exercise**: Add token signatures to Redis blacklists on logout.
*   **Debugging Task**: Fix authentication bypasses caused by expired blacklist cache keys.
*   **Interview Question**: How do you revoke stateless JWT access keys before expiration?
*   **Quiz**: What cache setting configures expiration times? (Answer: TTL).

### Lesson 17: Double-Submit CSRF Token Check
*   **Topic**: CSRF prevention.
*   **Objectives**: Implement CSRF checks on mutating requests.
*   **Files to Study**: [security_middleware.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/security_middleware.py).
*   **APIs**: `POST`, `PUT`, `PATCH`, `DELETE` routes.
*   **Database**: None.
*   **Hands-on Exercise**: Add validation checks comparing CSRF headers with cookie parameters.
*   **Debugging Task**: Fix authorization errors on API mutation requests.
*   **Interview Question**: How does double-submit validation protect routes from CSRF attacks?
*   **Quiz**: Does double-submit verification require database checks? (Answer: No).

### Lesson 18: MFA TOTP Key Validations
*   **Topic**: Multi-factor authentication.
*   **Objectives**: Implement TOTP validation checks.
*   **Files to Study**: [auth_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/auth_service.py).
*   **APIs**: `POST /auth/mfa/verify`.
*   **Database**: `users`.
*   **Hands-on Exercise**: Implement sliding window checks to tolerate device clock drifts.
*   **Debugging Task**: Fix validation errors caused by time drift between user devices and servers.
*   **Interview Question**: How does a TOTP token verify keys without database checks?
*   **Quiz**: What is the default lifespan step of a TOTP code? (Answer: 30 seconds).

---

## Phase 4: Prerequisite Graphs & Topological Sorting (Lessons 19-24)

### Lesson 19: Directed Acyclic Graph (DAG) Structures
*   **Topic**: Content graph design.
*   **Objectives**: Represent topics as graph nodes.
*   **Files to Study**: [knowledge_graph.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/knowledge_graph.py).
*   **APIs**: None.
*   **Database**: `topics`, `topic_prerequisites`.
*   **Hands-on Exercise**: Create a function to convert topics into graph nodes.
*   **Debugging Task**: Identify circular prerequisite loop relationships.
*   **Interview Question**: What is a Directed Acyclic Graph (DAG)?
*   **Quiz**: Which database relationship models prerequisite loops? (Answer: Self-referential many-to-many).

### Lesson 20: Topological Sort Algorithm
*   **Topic**: Path sorting.
*   **Objectives**: Sort topic prerequisites topologically.
*   **Files to Study**: [knowledge_graph.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/knowledge_graph.py).
*   **APIs**: None.
*   **Database**: None.
*   **Hands-on Exercise**: Implement Kahn's algorithm to sort topic prerequisite lists.
*   **Debugging Task**: Fix infinite loops caused by dependency cycles.
*   **Interview Question**: What is the computational complexity of topological sorting? (Answer: $O(V+E)$).
*   **Quiz**: Can topological sorting process cyclic graphs? (Answer: No).

### Lesson 21: Database Prerequisite Recursive CTEs
*   **Topic**: Advanced SQL queries.
*   **Objectives**: Query graph prerequisites using database CTEs.
*   **Files to Study**: [postgres_tenant_rls.sql](file:///home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls.sql).
*   **APIs**: None.
*   **Database**: `topic_prerequisites`.
*   **Hands-on Exercise**: Write a recursive CTE query to fetch prerequisites for a topic.
*   **Debugging Task**: Fix recursion limit errors on deep graph queries.
*   **Interview Question**: What is the advantage of recursive database CTEs over in-memory loops?
*   **Quiz**: What command defines SQL CTEs? (Answer: `WITH RECURSIVE`).

### Lesson 22: Content Circular Dependency Protection
*   **Topic**: Graph validation.
*   **Objectives**: Prevent prerequisite cycle creation.
*   **Files to Study**: [knowledge_graph.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/knowledge_graph.py) and [topic_question_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/topic_question_service.py).
*   **APIs**: `POST /topics/{topic_id}/prerequisites`.
*   **Database**: `topic_prerequisites`.
*   **Hands-on Exercise**: Add validation checks to reject prerequisite relationships that create loops.
*   **Debugging Task**: Fix routing lockups caused by circular dependencies.
*   **Interview Question**: How do you detect cycles in directed graphs?
*   **Quiz**: Which search algorithm detects cycles? (Answer: Depth-First Search).

### Lesson 23: Roadmap Node State Machine
*   **Topic**: Learner progress.
*   **Objectives**: Manage step states (`locked`, `active`, `completed`).
*   **Files to Study**: [roadmap_routes.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/presentation/roadmap_routes.py).
*   **APIs**: `PUT /roadmap/steps/{step_id}/complete`.
*   **Database**: `roadmap_steps`.
*   **Hands-on Exercise**: Write a function to unlock dependent steps when prerequisites are met.
*   **Debugging Task**: Fix issues where step status gets stuck in a `locked` state.
*   **Interview Question**: How do you manage transactional integrity during bulk status updates?
*   **Quiz**: What is the default status of a new roadmap step? (Answer: `locked`).

### Lesson 24: Pre-calculated View Aggregations
*   **Topic**: View optimizations.
*   **Objectives**: Query analytics using materialized views.
*   **Files to Study**: [postgres_tenant_rls.sql](file:///home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls.sql) and [precomputed_analytics_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/precomputed_analytics_service.py).
*   **APIs**: `GET /analytics/summary`.
*   **Database**: `tenant_analytics_mv`.
*   **Hands-on Exercise**: Write a script to refresh materialized view tables.
*   **Debugging Task**: Fix stale analytics data caused by refresh task failures.
*   **Interview Question**: What is the difference between standard and materialized database views?
*   **Quiz**: What command updates materialized views? (Answer: `REFRESH MATERIALIZED VIEW`).

---

## Phase 5: Adaptive Testing Engine (Lessons 25-30)

### Lesson 25: Item Response Theory (IRT) Baseline
*   **Topic**: Score modeling.
*   **Objectives**: Understand IRT score calculations.
*   **Files to Study**: [adaptive_testing_engine.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/adaptive_testing_engine.py).
*   **APIs**: None.
*   **Database**: None.
*   **Hands-on Exercise**: Write a function to calculate the probability of a correct answer based on IRT.
*   **Debugging Task**: Fix score calculations that fail to update student ability metrics.
*   **Interview Question**: How does IRT differ from raw percentage scoring?
*   **Quiz**: What parameter represents student ability? (Answer: Theta $\theta$).

### Lesson 26: Question Difficulty Selection
*   **Topic**: Adaptive selection.
*   **Objectives**: Select questions matching ability levels.
*   **Files to Study**: [adaptive_testing_engine.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/adaptive_testing_engine.py).
*   **APIs**: `GET /diagnostic/next-question`.
*   **Database**: `questions`.
*   **Hands-on Exercise**: Implement selection logic to match questions to student ability scores.
*   **Debugging Task**: Fix empty question selections caused by narrow search ranges.
*   **Interview Question**: How do you prevent selection loops when student ability is constant?
*   **Quiz**: What parameter represents question difficulty? (Answer: $b$).

### Lesson 27: Quiz Response Verification & scoring
*   **Topic**: Diagnostic scoring.
*   **Objectives**: Record quiz responses and update scores.
*   **Files to Study**: [diagnostic_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/diagnostic_service.py).
*   **APIs**: `POST /diagnostic/submit`.
*   **Database**: `user_answers`, `diagnostic_tests`.
*   **Hands-on Exercise**: Update diagnostic test states on question submissions.
*   **Debugging Task**: Fix double-submit issues that record responses twice.
*   **Interview Question**: How do you handle database transaction rollbacks during scoring failures?
*   **Quiz**: What table logs raw quiz answers? (Answer: `user_answers`).

### Lesson 28: Diagnostic Timer Enforcement
*   **Topic**: Time constraints.
*   **Objectives**: Enforce quiz question timers.
*   **Files to Study**: [test_diagnostic_timer_enforcement.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/test_diagnostic_timer_enforcement.py).
*   **APIs**: `POST /diagnostic/submit`.
*   **Database**: `diagnostic_tests`.
*   **Hands-on Exercise**: Implement verification logic to reject submissions after timers expire.
*   **Debugging Task**: Fix timing errors caused by network latency on route submissions.
*   **Interview Question**: How do you handle timing validation errors without affecting UX?
*   **Quiz**: What status represents expired answer attempts? (Answer: `timeout`).

### Lesson 29: Student Mastery Calculations
*   **Topic**: Progress tracking.
*   **Objectives**: Calculate student topic mastery.
*   **Files to Study**: [precomputed_analytics_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/precomputed_analytics_service.py).
*   **APIs**: `GET /analytics/mastery`.
*   **Database**: `topic_scores`.
*   **Hands-on Exercise**: Write a script to calculate student mastery across topic prerequisites.
*   **Debugging Task**: Fix mastery score calculation discrepancies in student dashboards.
*   **Interview Question**: How does mastery scoring guide adaptive roadmap updates?
*   **Quiz**: What table stores active student topic scores? (Answer: `topic_scores`).

### Lesson 30: Diagnostic Pool Expansion
*   **Topic**: Data management.
*   **Objectives**: Manage question pools.
*   **Files to Study**: [topic_question_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/topic_question_service.py).
*   **APIs**: `POST /topics/{topic_id}/questions`.
*   **Database**: `questions`.
*   **Hands-on Exercise**: Write a route script to import quiz questions in bulk.
*   **Debugging Task**: Resolve database constraint failures during bulk imports.
*   **Interview Question**: How do you maintain database integrity during bulk imports?
*   **Quiz**: Which format is used for bulk imports? (Answer: CSV/JSON).

---

## Phase 6: Real-time WebSockets & Redis Pub/Sub (Lessons 31-36)

### Lesson 31: WebSocket Gateway Initialization
*   **Topic**: Realtime connections.
*   **Objectives**: Configure WebSocket connection handlers.
*   **Files to Study**: [main.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/main.py).
*   **APIs**: `/ws/chat` and `/ws/alerts`.
*   **Database**: None.
*   **Hands-on Exercise**: Write connection handlers to verify JWT keys on WebSocket requests.
*   **Debugging Task**: Fix authentication errors that drop WebSocket connections.
*   **Interview Question**: How do you verify credentials on persistent WebSocket connections?
*   **Quiz**: What protocol manages WebSockets? (Answer: WS/WSS).

### Lesson 32: Redis Pub/Sub Event Bus
*   **Topic**: Realtime scaling.
*   **Objectives**: Configure event publishing with Redis.
*   **Files to Study**: [distributed_bus.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/realtime/distributed_bus.py).
*   **APIs**: None.
*   **Database**: Redis key store.
*   **Hands-on Exercise**: Write a class to publish events to Redis channels.
*   **Debugging Task**: Fix connection dropped events in the Redis Pub/Sub module.
*   **Interview Question**: Why use Redis Pub/Sub for WebSockets?
*   **Quiz**: Does Redis Pub/Sub persist event payloads? (Answer: No).

### Lesson 33: WebSocket Heartbeat Checks
*   **Topic**: Connection health.
*   **Objectives**: Terminate dead WebSocket connections.
*   **Files to Study**: [distributed_bus.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/realtime/distributed_bus.py).
*   **APIs**: WebSocket connection routes.
*   **Database**: None.
*   **Hands-on Exercise**: Implement client ping/pong routines to verify connection health.
*   **Debugging Task**: Fix server memory leaks caused by stale, unclosed connections.
*   **Interview Question**: How do you prevent connection leaks on server runtimes?
*   **Quiz**: What is the default interval for connection checks? (Answer: 30 seconds).

### Lesson 34: Realtime Dashboard Telemetry
*   **Topic**: Live dashboards.
*   **Objectives**: Push telemetry metrics in real-time.
*   **Files to Study**: [distributed_bus.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/realtime/distributed_bus.py).
*   **APIs**: `/ws/analytics`.
*   **Database**: `learning_events`.
*   **Hands-on Exercise**: Write a script to broadcast telemetry events to WebSocket channels.
*   **Debugging Task**: Debug client UI performance lag caused by high telemetry frequencies.
*   **Interview Question**: How do you optimize high-frequency updates on frontend dashboards?
*   **Quiz**: Which React hook manages WebSocket state? (Answer: `useEffect`).

### Lesson 35: Redis Sentinel Connection Pools
*   **Topic**: Cache availability.
*   **Objectives**: Configure Redis Sentinel connections.
*   **Files to Study**: Cache service configurations.
*   **APIs**: None.
*   **Database**: Redis sentinel nodes.
*   **Hands-on Exercise**: Configure connection pools to automatically failover to backup nodes.
*   **Debugging Task**: Fix connection errors during master node failover runs.
*   **Interview Question**: How does Redis Sentinel manage high availability?
*   **Quiz**: What node is promoted on master node crashes? (Answer: Replica).

### Lesson 36: Horizontal Scalability of Realtime Servers
*   **Topic**: Websocket scaling.
*   **Objectives**: Scale WebSocket connections horizontally.
*   **Files to Study**: [k8s/api.yaml](file:///home/charan_derangula/projects/intelligentSystems/k8s/api.yaml).
*   **APIs**: All WebSocket endpoints.
*   **Database**: Redis Pub/Sub cluster.
*   **Hands-on Exercise**: Configure Kubernetes replica sets to scale WebSocket pods.
*   **Debugging Task**: Fix message delivery issues when users are connected to different pods.
*   **Interview Question**: How does Redis Pub/Sub coordinate messages across replica pods?
*   **Quiz**: Which proxy gateway routes WebSocket connections? (Answer: Nginx).

---

## Phase 7: AI Microservice & Agent Routing (Lessons 37-42)

### Lesson 37: Decoupled AI Microservice Boundary
*   **Topic**: AI architecture.
*   **Objectives**: Understand AI microservice structures.
*   **Files to Study**: [ai_service/service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py) and [ai_service/main.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/main.py).
*   **APIs**: `POST /ai/chat`.
*   **Database**: None.
*   **Hands-on Exercise**: Add new endpoint configurations to the AI microservice.
*   **Debugging Task**: Fix timeout errors on AI service routes.
*   **Interview Question**: Why decouple the AI engine into a separate microservice?
*   **Quiz**: What framework runs the AI microservice? (Answer: FastAPI).

### Lesson 38: Supervisor-Specialist Agent Routing
*   **Topic**: Agent routing.
*   **Objectives**: Route prompts dynamically to specialized agents.
*   **Files to Study**: [ai_service/service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py) and [prompts.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/prompts.py).
*   **APIs**: Chat routing endpoints.
*   **Database**: None.
*   **Hands-on Exercise**: Write custom keyword rules to route prompts to a new agent.
*   **Debugging Task**: Fix routing checks that fail to assign inputs to the correct agent.
*   **Interview Question**: How does specialized agent routing reduce LLM hallucinations?
*   **Quiz**: What method manages agent assignments? (Answer: `_route_agents`).

### Lesson 39: AI JSON Schema Synthesis
*   **Topic**: Structured outputs.
*   **Objectives**: Synthesize agent responses into structured JSON.
*   **Files to Study**: [ai_service/service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py) and [schemas.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/schemas.py).
*   **APIs**: AI synthesis routes.
*   **Database**: None.
*   **Hands-on Exercise**: Add custom properties to the synthesis JSON response schemas.
*   **Debugging Task**: Debug JSON parsing errors caused by unstructured LLM outputs.
*   **Interview Question**: How do you enforce structured JSON outputs from LLM APIs?
*   **Quiz**: Which library parses response schemas? (Answer: Pydantic).

### Lesson 40: Input Guardrails & Safety Audits
*   **Topic**: AI security.
*   **Objectives**: Filter user prompts for injection threats.
*   **Files to Study**: [guardrails.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/guardrails.py).
*   **APIs**: `POST /ai/chat`.
*   **Database**: None.
*   **Hands-on Exercise**: Write validation rules to identify and block prompt injection phrases.
*   **Debugging Task**: Fix false positives in safety filters that block valid student queries.
*   **Interview Question**: What is a prompt injection attack?
*   **Quiz**: Which function checks for prompt injection keywords? (Answer: `injection_hints`).

### Lesson 41: Deterministic Tutoring Fallbacks
*   **Topic**: System reliability.
*   **Objectives**: Implement fallback systems for LLM failures.
*   **Files to Study**: [ai_service/service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py).
*   **APIs**: Chat interface APIs.
*   **Database**: `topic_scores`.
*   **Hands-on Exercise**: Write a script to return precomputed tutoring suggestions if LLM APIs fail.
*   **Debugging Task**: Fix routing issues that fail to activate fallback modes when APIs timeout.
*   **Interview Question**: How do you guarantee service availability during LLM outages?
*   **Quiz**: What fallback method provides precomputed responses? (Answer: `_fallback_mentor_response`).

### Lesson 42: Chat History Context Optimization
*   **Topic**: Token management.
*   **Objectives**: Optimize context windows for chat histories.
*   **Files to Study**: [ai_service/service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py) and [config.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/config.py).
*   **APIs**: Chat history retrieval APIs.
*   **Database**: `mentor_chat_messages`.
*   **Hands-on Exercise**: Implement truncation logic to restrict history context to the last 5 conversations.
*   **Debugging Task**: Fix context limits errors caused by large prompt histories.
*   **Interview Question**: How do you balance conversation history detail with token limits?
*   **Quiz**: What setting controls prompt history limits? (Answer: max_tokens / history limit parameters).

---

## Phase 8: Transactional Outbox Sweeps & Celery (Lessons 43-48)

### Lesson 43: Transactional Outbox Fundamentals
*   **Topic**: Event consistency.
*   **Objectives**: Save events to outbox tables.
*   **Files to Study**: [outbox_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/outbox_service.py).
*   **APIs**: Mutating REST APIs.
*   **Database**: `outbox_events`.
*   **Hands-on Exercise**: Add custom properties to the outbox database schema.
*   **Debugging Task**: Fix database sync errors caused by uncommitted outbox transactions.
*   **Interview Question**: What is the transactional outbox pattern?
*   **Quiz**: What status represents new, unprocessed outbox events? (Answer: `PENDING`).

### Lesson 44: Celery Background Task Brokerage
*   **Topic**: Asynchronous tasks.
*   **Objectives**: Configure Celery task runners.
*   **Files to Study**: [celery_app.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/celery_app.py) and [jobs_tasks.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/test_jobs_tasks.py).
*   **APIs**: None.
*   **Database**: Redis broker nodes.
*   **Hands-on Exercise**: Create a Celery task to verify cache synchronization.
*   **Debugging Task**: Fix connection errors between Celery workers and Redis.
*   **Interview Question**: How does Celery coordinate tasks using Redis?
*   **Quiz**: Which queue manager runs periodic tasks? (Answer: Celery Beat).

### Lesson 45: Outbox Event Sweep Jobs
*   **Topic**: Event dispatch.
*   **Objectives**: Dispatch pending outbox events.
*   **Files to Study**: [outbox_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/outbox_service.py).
*   **APIs**: None.
*   **Database**: `outbox_events`.
*   **Hands-on Exercise**: Write a script to lock, process, and clear pending outbox events.
*   **Debugging Task**: Fix processing stalls where events get stuck in a `PROCESSING` state.
*   **Interview Question**: How do you prevent multiple workers from processing the same outbox events?
*   **Quiz**: What query configuration skips locked rows? (Answer: `FOR UPDATE SKIP LOCKED`).

### Lesson 46: Exponential Retry Backoff
*   **Topic**: Error recovery.
*   **Objectives**: Implement backoff retries for failed tasks.
*   **Files to Study**: [test_outbox_retry_backoff.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/test_outbox_retry_backoff.py).
*   **APIs**: None.
*   **Database**: `outbox_events`.
*   **Hands-on Exercise**: Implement exponential retry backoff parameters for failed events.
*   **Debugging Task**: Fix infinite loops caused by missing retry limits.
*   **Interview Question**: What is exponential backoff?
*   **Quiz**: What is the default maximum retry count? (Answer: 5).

### Lesson 47: Idempotency Verification Keys
*   **Topic**: Event deduplication.
*   **Objectives**: Prevent duplicate event execution.
*   **Files to Study**: [outbox_repository_logic.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/test_outbox_repository_logic.py).
*   **APIs**: All event-consuming APIs.
*   **Database**: `processed_events`.
*   **Hands-on Exercise**: Implement idempotency checks using event ID signatures.
*   **Debugging Task**: Fix database inconsistencies caused by duplicate events.
*   **Interview Question**: How do you guarantee idempotent event processing?
*   **Quiz**: What database constraint enforces unique event execution? (Answer: Unique index on event ID).

### Lesson 48: Dead-Letter Queue (DLQ) Management
*   **Topic**: Error handling.
*   **Objectives**: Handle permanently failed events.
*   **Files to Study**: [outbox_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/outbox_service.py).
*   **APIs**: None.
*   **Database**: `outbox_events`.
*   **Hands-on Exercise**: Write a script to move permanently failed events to a DLQ and trigger alert notifications.
*   **Debugging Task**: Identify and recover events stuck in the DLQ.
*   **Interview Question**: How do you monitor and resolve DLQ errors in production?
*   **Quiz**: What status represents events moved to the DLQ? (Answer: `FAILED`).

---

## Phase 9: Observability, Metrics, & Alarms (Lessons 49-54)

### Lesson 49: Prometheus Exporter Implementation
*   **Topic**: Metrics collection.
*   **Objectives**: Expose metrics for Prometheus scraping.
*   **Files to Study**: [main.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/main.py) and [celery_observability.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/test_celery_observability.py).
*   **APIs**: `/metrics`.
*   **Database**: None.
*   **Hands-on Exercise**: Add a request latency counter to the API metrics endpoint.
*   **Debugging Task**: Fix missing metrics data caused by scraping endpoint timeouts.
*   **Interview Question**: How does Prometheus gather metrics?
*   **Quiz**: What port does the API metrics endpoint expose? (Answer: Port 8000 / target custom port).

### Lesson 50: Alertmanager Configs & Routes
*   **Topic**: Alert routing.
*   **Objectives**: Configure notification routing rules.
*   **Files to Study**: [alertmanager.yml](file:///home/charan_derangula/projects/intelligentSystems/monitoring/alertmanager/alertmanager.yml).
*   **APIs**: None.
*   **Database**: None.
*   **Hands-on Exercise**: Add custom email notification routes to Alertmanager configurations.
*   **Debugging Task**: Fix routing issues that fail to deliver high-priority alerts to operators.
*   **Interview Question**: How does Alertmanager de-duplicate and group alerts?
*   **Quiz**: Which channel delivers default alerts? (Answer: Webhook/Slack/PagerDuty).

### Lesson 51: Latency Alert Rules
*   **Topic**: Performance alerts.
*   **Objectives**: Create alert rules for request latency.
*   **Files to Study**: [alerts.yml](file:///home/charan_derangula/projects/intelligentSystems/monitoring/prometheus/alerts.yml).
*   **APIs**: None.
*   **Database**: None.
*   **Hands-on Exercise**: Add alert rules to detect when P95 request latency exceeds 1.5 seconds.
*   **Debugging Task**: Fix false alarms caused by temporary latency spikes.
*   **Interview Question**: Why use P95/P99 metrics instead of average latency for performance alerts?
*   **Quiz**: What Prometheus function calculates rate metrics over time? (Answer: `rate()`).

### Lesson 52: Grafana System Dashboards
*   **Topic**: Data visualization.
*   **Objectives**: Configure Grafana system dashboards.
*   **Files to Study**: Dashboard provisioning configurations.
*   **APIs**: None.
*   **Database**: None.
*   **Hands-on Exercise**: Create a dashboard panel to monitor active database connection counts.
*   **Debugging Task**: Fix panels that fail to load data due to metrics query syntax errors.
*   **Interview Question**: How do you design dashboard layouts to help operators debug issues quickly during incidents?
*   **Quiz**: What language is used to query Prometheus data? (Answer: PromQL).

### Lesson 53: Log Rotation & Volume Rules
*   **Topic**: Log management.
*   **Objectives**: Prevent log files from filling up disk volumes.
*   **Files to Study**: [logging_middleware.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/test_logging_middleware.py).
*   **APIs**: None.
*   **Database**: None.
*   **Hands-on Exercise**: Configure log rotation rules in the application's logging configurations.
*   **Debugging Task**: Fix container storage crashes caused by unrotated logs.
*   **Interview Question**: How do you manage log volume size constraints in production?
*   **Quiz**: Which command cleans up historical log files? (Answer: logrotate / custom purge script).

### Lesson 54: Distributed Tracing & Span Identifiers
*   **Topic**: Request tracing.
*   **Objectives**: Trace requests across microservice boundaries.
*   **Files to Study**: [main.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/main.py) and [ai_service/main.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/main.py).
*   **APIs**: All endpoints.
*   **Database**: None.
*   **Hands-on Exercise**: Inject unique trace IDs into headers to track requests across services.
*   **Debugging Task**: Fix missing trace details caused by headers being dropped between service calls.
*   **Interview Question**: What is distributed tracing?
*   **Quiz**: What header standard passes trace contexts? (Answer: W3C Trace Context / `traceparent`).

---

## Phase 10: Kubernetes, Scaling, & Redesign (Lessons 55-60)

### Lesson 55: Kubernetes Manifest Orchestration
*   **Topic**: Container deployments.
*   **Objectives**: Deploy application containers to Kubernetes.
*   **Files to Study**: [api.yaml](file:///home/charan_derangula/projects/intelligentSystems/k8s/api.yaml) and [ingress.yaml](file:///home/charan_derangula/projects/intelligentSystems/k8s/ingress.yaml).
*   **APIs**: None.
*   **Database**: None.
*   **Hands-on Exercise**: Deploy updated API and frontend configurations to a local minikube cluster.
*   **Debugging Task**: Fix pod launch failures caused by ConfigMap validation errors.
*   **Interview Question**: How do you manage secrets securely in Kubernetes?
*   **Quiz**: What object manages path-based routing in Kubernetes? (Answer: Ingress).

### Lesson 56: Horizontal Pod Autoscaler (HPA) Tuning
*   **Topic**: Auto-scaling.
*   **Objectives**: Configure container autoscaling rules.
*   **Files to Study**: [hpa.yaml](file:///home/charan_derangula/projects/intelligentSystems/k8s/hpa.yaml).
*   **APIs**: None.
*   **Database**: None.
*   **Hands-on Exercise**: Configure HPA rules to scale pod counts based on CPU usage metrics.
*   **Debugging Task**: Fix autoscaling lags during sudden traffic spikes.
*   **Interview Question**: How do you scale pods using custom application metrics?
*   **Quiz**: What Kubernetes controller scales pod counts dynamically? (Answer: Horizontal Pod Autoscaler).

### Lesson 57: Zero-Downtime Rolling Updates
*   **Topic**: Deployment strategies.
*   **Objectives**: Deploy updates without downtime.
*   **Files to Study**: [api.yaml](file:///home/charan_derangula/projects/intelligentSystems/k8s/api.yaml).
*   **APIs**: None.
*   **Database**: None.
*   **Hands-on Exercise**: Configure liveness and readiness probes to manage rolling update transitions.
*   **Debugging Task**: Fix connection drops during rolling deployments.
*   **Interview Question**: How do liveness and readiness probes manage traffic routing during updates?
*   **Quiz**: What update policy launches new pods before terminating old ones? (Answer: RollingUpdate).

### Lesson 58: Materialized View Refresh Schedules
*   **Topic**: Performance updates.
*   **Objectives**: Schedule database view refreshes.
*   **Files to Study**: [precomputed_analytics_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/precomputed_analytics_service.py) and [postgres_tenant_rls.sql](file:///home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls.sql).
*   **APIs**: None.
*   **Database**: `tenant_analytics_mv`.
*   **Hands-on Exercise**: Write a Celery task to refresh materialized views on a custom schedule.
*   **Debugging Task**: Fix transaction deadlock issues during concurrent view refreshes.
*   **Interview Question**: How do you refresh database views without locking tables?
*   **Quiz**: What option allows views to be read during refreshes? (Answer: `CONCURRENTLY`).

### Lesson 59: Neo4j Graph Integration Redesign
*   **Topic**: Database migration.
*   **Objectives**: Design a migration to a graph database.
*   **Files to Study**: [knowledge_graph.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/knowledge_graph.py) and [scalability_review.md](file:///home/charan_derangula/.gemini/antigravity-ide/brain/8a38af85-4200-4919-acb6-cd20f83ccb71/scalability_review.md).
*   **APIs**: None.
*   **Database**: Neo4j Graph DB.
*   **Hands-on Exercise**: Write Cypher queries to fetch prerequisite nodes for a topic.
*   **Debugging Task**: Optimize slow Cypher queries by adding node index configurations.
*   **Interview Question**: Why use a graph database instead of a relational database for prerequisite mappings?
*   **Quiz**: What language queries Neo4j databases? (Answer: Cypher).

### Lesson 60: Multi-Region Database Replica Failovers
*   **Topic**: Disaster recovery.
*   **Objectives**: Design multi-region database failover configurations.
*   **Files to Study**: [reliability_runbook.md](file:///home/charan_derangula/projects/intelligentSystems/docs/reliability_runbook.md) and [cto_review.md](file:///home/charan_derangula/.gemini/antigravity-ide/brain/8a38af85-4200-4919-acb6-cd20f83ccb71/cto_review.md).
*   **APIs**: None.
*   **Database**: Multi-region PostgreSQL clusters.
*   **Hands-on Exercise**: Write a failover runbook to promote replica nodes in backup regions.
*   **Debugging Task**: Fix write errors caused by read-only replica status designations after failover.
*   **Interview Question**: How do you prevent data loss during database failovers across regions?
*   **Quiz**: What is the target recovery time limit metric? (Answer: RTO).
