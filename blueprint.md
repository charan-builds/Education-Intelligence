# Universal Learning Intelligence Platform

## Project Documentation and Progress Audit Report

## 1. Executive Overview

- **Project Name:** Universal Learning Intelligence Platform
- **Project Type:** Multi-Tenant SaaS Learning Platform
- **Primary Goal:** Diagnose learner knowledge gaps, identify weak concepts, generate personalized roadmaps, and track measurable learning progress across institutions and independent learners.
- **Current State:** Strong backend foundation with production-oriented architecture, broad API coverage, async job processing, monitoring, and a growing multi-panel frontend. Core learner flows are implemented, but some platform capabilities are still partial or staged for future rollout.

### What this project does

- Conducts diagnostic tests against a topic/question bank
- Scores learner performance by topic
- Detects weak concepts and missing prerequisites
- Generates personalized learning roadmaps
- Tracks roadmap progress and learning signals over time
- Supports multiple tenants such as colleges, schools, companies, and personal learner workspaces

### Why this project is strong

- Clean layered backend architecture
- Good separation of business logic from delivery and persistence
- Multi-tenant design with tenant-aware routing, repositories, and growing RLS coverage
- Production-minded infrastructure including Celery, Redis, monitoring, outbox reliability, Docker, and Kubernetes manifests

## 2. Resume / Interview Summary

### 3-4 line project summary

- Built a production-oriented **multi-tenant learning intelligence platform** using **FastAPI, PostgreSQL, SQLAlchemy, Alembic, Redis, Celery, and Next.js**.
- Implemented adaptive diagnostics, rule-based recommendation logic, personalized roadmap generation, learner analytics, and role-based dashboards for students, teachers, admins, and super admins.
- Designed the backend using a **Route -> Service -> Engine -> Repository -> Database** architecture with JWT auth, RBAC, tenant-aware data access, async jobs, outbox reliability, and observability tooling.
- Added frontend panel foundations and production deployment assets including Docker Compose, Kubernetes manifests, Prometheus, Grafana, and Nginx gateway configuration.

### One-line elevator pitch

- A multi-tenant SaaS platform that turns learner assessment data into personalized learning roadmaps, analytics, and actionable intervention workflows.

## 3. Product Vision

- Move learning from generic content delivery to adaptive, intelligence-driven progression.
- Help institutions and individual learners understand:
  - what they know
  - what they do not know
  - what they must learn next
  - how their progress is evolving over time

### Target users

- Super admins operating the platform
- Institution admins managing tenant-specific users and content
- Teachers monitoring cohort performance
- Students following guided roadmaps
- Independent learners using a personal workspace model

## 4. Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy async ORM
- Alembic migrations
- Celery for background jobs
- Redis for broker/cache support

### Database

- PostgreSQL

### Frontend

- React / Next.js frontend workspace
- Role-based dashboards and route groups for multiple panels

### Authentication and Security

- JWT-based authentication
- Refresh-token session handling
- Role-based access control
- Tenant-aware data access
- Partial PostgreSQL RLS rollout

### Operations and Observability

- Docker Compose local stack
- Kubernetes manifests
- Nginx gateway
- Prometheus
- Grafana
- Alertmanager

## 5. Architecture Overview

### Architectural style

- **Layered modular monolith**
- Core request path follows:

`Route -> Service -> Engine -> Repository -> Database`

### Layer responsibilities

- **Route layer**
  - Exposes REST APIs
  - Validates request/response schemas
  - Applies auth, rate limits, and role guards

- **Service layer**
  - Owns use-case orchestration
  - Coordinates repositories, engines, feature flags, notifications, and async workflows

- **Engine layer**
  - Encapsulates core domain logic
  - Handles adaptive testing, recommendation logic, prerequisite reasoning, weakness modeling, knowledge graph traversal, and learning profile inference

- **Repository layer**
  - Centralizes database queries and persistence rules
  - Applies tenant-aware filtering and data access patterns

- **Database layer**
  - PostgreSQL with relational modeling, materialized views, async access, migrations, and emerging row-level security

### Key design decision

- Business logic is intentionally kept out of route handlers and repositories.
- This makes the platform easier to test, safer to evolve, and more scalable as new panels and services are added.

## 6. Core Service and Engine Design

### `diagnostic_service`

- **Purpose**
  - Manages the full diagnostic lifecycle

- **How it works**
  - Starts or resumes a diagnostic test
  - Selects the next question using adaptive testing logic
  - Scores answers using domain rules
  - Persists answer state and diagnostic test state
  - Finalizes results and triggers roadmap generation workflows

- **Key supporting engines/services**
  - `AdaptiveTestingEngine`
  - `AdaptiveEngineService`
  - `WeaknessModelingEngine`
  - `RecommendationService`
  - learning event, gamification, retention, skill-vector, and outbox services

- **Status**
  - **Completed for backend core flow**
  - Advanced enrichment is present but some surrounding features remain partial

### `recommendation_engine`

- **Purpose**
  - Determines which weak topics should be prioritized next

- **How it works**
  - Uses a rule-based engine by default
  - Can route to ML-backed recommendation flow when feature flags and async AI result paths are enabled
  - Orders weak topics while preserving prerequisite dependencies

- **Current behavior**
  - Rule-based recommendation is the production-ready default
  - ML recommendation path exists as an extensibility hook, not as the primary proven path

- **Status**
  - **Rule-based engine completed**
  - **ML-driven recommendation partial**

### `roadmap_service`

- **Purpose**
  - Converts diagnostic outcomes into actionable learning plans

- **How it works**
  - Reads topic scores from a completed diagnostic
  - Pulls prerequisite edges from the topic graph
  - Builds a learner profile from timing and accuracy signals
  - Chooses recommended target topics
  - Expands prerequisites using the knowledge graph
  - Generates roadmap steps with priorities, deadlines, rationale, and progression states
  - Triggers notifications and analytics refresh jobs

- **Status**
  - **Completed for roadmap generation and learner updates**
  - Adaptive refresh and ecosystem integrations are **partial**

### Analytics modules

- **Purpose**
  - Provide learner, tenant, topic, and platform analytics

- **How they work**
  - Live service methods compute analytics when needed
  - Precomputed analytics snapshots and materialized views improve read performance
  - Background jobs refresh snapshots asynchronously
  - Dashboards consume summary endpoints for panel experiences

- **Status**
  - **Completed for core analytics APIs**
  - **Partial for freshness guarantees and full production-hardening**

## 7. Core Modules

### Authentication Module

- **What it does**
  - User registration, login, logout, refresh, invite flows, password reset, email verification, MFA, session tracking

- **How it works**
  - JWT access and refresh tokens
  - Cookie support plus bearer token support
  - Password hashing with bcrypt
  - Session and token lifecycle persistence

- **Status**
  - **Completed**

### Tenant Management

- **What it does**
  - Creates and lists tenants
  - Supports tenant types including platform, college, school, company, and personal

- **How it works**
  - Tenant-scoped repository and role checks
  - Super admin governance through dedicated APIs and dashboard paths

- **Status**
  - **Completed for backend core management**
  - **Partial for full end-to-end governance workflows**

### User Management

- **What it does**
  - Creates tenant users, lists users, supports profile completion and updates

- **How it works**
  - Uses role guards and tenant scoping
  - Frontend admin flows are present for major operations

- **Status**
  - **Completed**

### Topic Knowledge Graph

- **What it does**
  - Models topics, prerequisites, topic-skill relations, and graph-based reasoning

- **How it works**
  - Maintains prerequisite edges
  - Generates graph snapshots and topic reasoning output
  - Supports dependency-depth and semantic relationship analysis

- **Status**
  - **Completed for core graph and reasoning**
  - **Partial for advanced semantic enrichment**

### Diagnostic Engine

- **What it does**
  - Administers adaptive diagnostics and scores answers

- **How it works**
  - Selects next question by topic weakness and target difficulty
  - Supports question types like `multiple_choice` and `short_text`
  - Persists answer attempts, timing, and accuracy

- **Status**
  - **Completed**

### Recommendation Engine

- **What it does**
  - Chooses weak topics and required foundations

- **How it works**
  - Primarily threshold and prerequisite driven
  - Optional async AI/ML path exists behind feature-controlled behavior

- **Status**
  - **Completed for rule-based recommendations**
  - **Partial for ML**

### Roadmap Generator

- **What it does**
  - Produces roadmap records and ordered roadmap steps

- **How it works**
  - Merges diagnostic topic scores, prerequisite paths, weakness clusters, and profile traits

- **Status**
  - **Completed**

### Progress Tracking

- **What it does**
  - Tracks roadmap step completion, active progress, and event-based learner updates

- **How it works**
  - Student roadmap step updates
  - Real-time notifications
  - Learning events, retention, and gamification hooks

- **Status**
  - **Completed for core roadmap progress**
  - **Partial for richer cross-feature consistency**

### Analytics

- **What it does**
  - Surfaces overview metrics, roadmap progress, topic mastery, student performance, topic performance, retention, and platform summaries

- **How it works**
  - Query-time analytics plus snapshot/materialized-view refresh jobs

- **Status**
  - **Completed for major APIs**
  - **Partial for full freshness, global consistency, and operational maturity**

## 8. Panels

## Super Admin Panel

### Purpose

- Operate the platform globally across all tenants

### Features

- Tenant-level metrics and breakdowns
- Cross-tenant learner analytics
- Outbox/dead-letter visibility
- Platform health and enabled feature signal visibility
- Tenant creation/listing APIs on backend

### Current implementation status

- **Backend:** Completed
- **Frontend:** Partial to strong
- **Overall:** **Partial**

### Audit note

- The dashboard is implemented and meaningful, but broader global governance workflows are still less complete than the backend foundation suggests.

## Institution Admin Panel

### Purpose

- Operate a single tenant as a managed learning organization

### Features

- User creation and management
- Topic, question, prerequisite, and goal management
- Analytics overview
- Community moderation
- Feature flag controls

### Current implementation status

- **Backend:** Completed
- **Frontend:** Strong for dashboard and management flows
- **Overall:** **Completed / strong partial**

### Audit note

- This is one of the most mature non-learner panels in the repository.

## Teacher Panel

### Purpose

- Monitor cohort learning performance and intervene on struggling learners

### Features

- Cohort metrics
- Weak-topic clusters
- Retention trend visibility
- Student watchlist and top-student views
- Recommendation surfaces

### Current implementation status

- **Backend:** Completed for analytics access
- **Frontend:** Good dashboard coverage
- **Overall:** **Partial**

### Audit note

- Teacher analytics are present, but deeper classroom operations and detailed student drill-down workflows are not yet fully represented as complete end-to-end teacher tooling.

## Student Panel

### Purpose

- Deliver the main learner journey from diagnostic to roadmap to progress tracking

### Features

- Authentication
- Goal selection
- Diagnostic initiation, answering, next-question flow, and submission
- Diagnostic result retrieval
- Roadmap generation and viewing
- Roadmap step progress updates
- Dashboard analytics, mentor prompts, realtime activity, and progress storytelling UI

### Current implementation status

- **Backend:** Completed
- **Frontend:** Strong
- **Overall:** **Completed**

### Audit note

- Student experience is the clearest and most mature product path in the system.

## Independent Learner Panel

### Purpose

- Provide a self-serve personal learning workspace outside institutional administration

### Features

- Personal workspace tenant model
- Shared learner dashboard experience
- Goal, diagnostic, roadmap, and progress routes

### Current implementation status

- **Backend:** Partial to strong
- **Frontend:** Partial
- **Overall:** **Partial**

### Audit note

- Independent learner support exists conceptually and in routing, but the dashboard currently reuses the student panel rather than delivering a fully distinct product surface.

## Mentor Panel

### Purpose

- Support AI-assisted or guided mentoring workflows

### Features

- Mentor dashboard
- Learner selection
- Suggestions, notifications, focus topics, roadmap awareness
- Autonomous agent cycle trigger

### Current implementation status

- **Backend:** Partial
- **Frontend:** Partial
- **Overall:** **Partial**

### Audit note

- This panel is beyond the minimum requested scope, but it exists in the repo and is clearly still evolving.

## 9. Database Design

### Key tables

#### `tenants`

- Stores each tenant workspace
- Supports tenant type and subdomain
- Anchors all tenant-scoped data

#### `users`

- Stores account identity, role, profile fields, auth/security flags, and tenant ownership
- Supports roles including `super_admin`, `admin`, `teacher`, `mentor`, `student`, and `independent_learner`

#### `goals`

- Stores learning or career goals
- Tenant-scoped so different institutions can manage their own goals

#### `topics`

- Stores learning topics
- Includes fields that support graph indexing and hierarchy reasoning

#### `topic_prerequisites`

- Stores directed prerequisite relationships between topics
- Enables dependency tracing and roadmap sequencing

#### `questions`

- Stores assessment questions tied to topics
- Supports difficulty, question type, accepted answers, and answer options

#### `diagnostic_tests`

- Stores each learner diagnostic attempt
- Links a user to a goal and test lifecycle timestamps

#### `user_answers`

- Stores learner answers per question per diagnostic
- Captures score, accuracy, time taken, and attempt count

#### `roadmaps`

- Stores generated personalized plans
- Tracks generation status and error state

#### `roadmap_steps`

- Stores ordered learning steps within a roadmap
- Tracks difficulty, priority, deadline, step type, rationale, and progress status

### Relationship model

- One `tenant` has many `users`
- One `tenant` has many `goals` and `topics`
- One `topic` has many `questions`
- One `topic` can have many prerequisite edges through `topic_prerequisites`
- One `user` has many `diagnostic_tests`
- One `diagnostic_test` has many `user_answers`
- One `user` has many `roadmaps`
- One `roadmap` has many `roadmap_steps`

### Why this design works

- Normalized enough for correctness and queryability
- Strongly supports graph reasoning for learning paths
- Preserves auditability of each diagnostic and roadmap generation cycle
- Keeps tenant ownership explicit for SaaS isolation

## 10. Core Logic

### Diagnostic flow

`User -> Test -> Score -> Weak Topics -> Prerequisites -> Roadmap`

### Detailed explanation

- User starts a diagnostic for a selected goal
- Adaptive engine selects the next question
- Answers are scored with correctness and accuracy rules
- Topic-level scores are aggregated
- Weakness modeling identifies low-mastery areas
- Prerequisites are expanded to avoid skipping foundations
- Recommendation logic ranks what to learn next
- Roadmap service generates sequenced roadmap steps

### Recommendation logic

- Current production path is **rule-based**
- Broad logic:
  - low scores indicate weak topics
  - prerequisite chains are added before advanced topics
  - learner profile data can influence pacing and step construction

### Score-threshold interpretation

- Below threshold: weak / needs reinforcement
- Mid band: practicing / needs structured progression
- High score: mastered or ready to advance

## 11. Security Model

### JWT

- Access and refresh token flow is implemented
- Supports cookies and bearer token transport
- Includes invite, email verification, and password reset token types

### RBAC

- Role-based access is enforced at route and permission levels
- Roles include platform and tenant-specific responsibilities

### Tenant isolation

- Tenant-aware filtering is implemented in repositories and service flows
- PostgreSQL RLS exists for a subset of tables
- Current state is **mixed-mode isolation**, not yet universal RLS coverage

### Security status

- **JWT:** Completed
- **RBAC:** Completed
- **Tenant isolation:** Partial

## 12. Testing Status

### Current testing posture

- Large backend test suite exists
- Repository contains **98 backend test files**
- Coverage includes auth, diagnostics, analytics, roadmap generation, tenant isolation, outbox flows, feature flags, community, mentor, AI, and route contracts

### Verified during this audit

- Focused backend run passed:
  - `test_auth.py`
  - `test_diagnostic_routes.py`
  - `test_roadmap_routes.py`
  - `test_analytics_routes.py`
- Result: **27 tests passed**

### Testing categories

- **Unit testing**
  - Domain engines, rules, and service logic

- **API testing**
  - Route contracts and auth-protected endpoints

- **Integration testing**
  - Tenant isolation, repository behavior, outbox, analytics refresh, and service interactions

### Testing assessment

- **Backend testing:** Strong
- **Frontend testing:** Partial
- **End-to-end production validation:** Partial

## 13. Deployment Status

### Implemented deployment assets

- Docker Compose stack
- Nginx API gateway
- Separate frontend, backend, AI service, worker, beat, Postgres, Redis, monitoring containers
- Kubernetes manifests for API, frontend, AI service, workers, ingress, HPA, PDB, network policies, config, and cron jobs
- CI/CD workflow references

### What appears deployable now

- Backend API
- Celery workers and beat
- PostgreSQL and Redis-backed local environment
- Frontend containerized deployment
- Monitoring stack

### What is clearly local/dev-ready

- Full Docker Compose setup
- Local seed data and demo users
- Monitoring stack for local ops validation

### What is still pending for true production rollout

- Final secret management and environment hardening
- Confirmed live cloud deployment state
-  