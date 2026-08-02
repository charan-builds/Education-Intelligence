# Independent Learner Panel

## Universal Learning Intelligence Platform

## System Document and Implementation Audit

**Panel Scope:** Independent Learner Panel  
**Platform Type:** Multi-tenant SaaS  
**Backend:** FastAPI + SQLAlchemy + PostgreSQL  
**Auth:** JWT + refresh sessions  
**Frontend:** React / Next.js  
**Audit Basis:** This document is based on the current repository structure and code inspection, not just target-state architecture.

---

## 1. Panel Overview

### What is the Independent Learner Panel

The Independent Learner Panel is the self-service workspace for users who register directly on the platform without belonging to a school, college, company, or managed tenant. It gives an individual learner a personal workspace where they can:

- create an account
- enter a self-directed learning flow
- select a goal
- take a diagnostic
- detect weak topics
- generate a roadmap
- track progress over time

In the current codebase, this panel is implemented primarily as:

- role: `independent_learner`
- tenant model: `personal`
- frontend route group: `/independent-learner/*`
- backend behavior: mostly shared with the student learner services

### Who uses it

Typical users:

- self-learners preparing for careers, exams, or technical upskilling
- professionals reskilling outside an institution
- learners testing the platform before joining an organization
- B2C users in a direct subscription or freemium model

### How it differs from the Student Panel

The Student Panel is institution-linked. The Independent Learner Panel is self-owned.

Key differences:

- Student users belong to an institutional tenant and usually have admin/teacher context behind them.
- Independent learners are auto-provisioned into a personal tenant during registration.
- Student experiences may depend on institution-managed goals, content, analytics, mentor assignment, and admin operations.
- Independent learners need self-serve onboarding, default goals/content availability, and personal workspace defaults.

Current repo reality:

- Frontend routes are separated.
- Backend learner logic is mostly shared between `student` and `independent_learner`.
- The independent learner panel is a role-specific wrapper, not yet a deeply separate product slice.

### Business purpose

This panel enables direct-to-consumer growth and platform adoption beyond institutions.

Business value:

- opens B2C revenue path
- reduces dependence on institutional sales cycles
- creates individual usage data for recommendation and roadmap engines
- supports low-friction trial-to-paid conversion
- provides a personal workspace that can later be upgraded or linked to a managed tenant

---

## 2. Complete User Flow

## 2.1 Product Journey

### 1. Register

User enters:

- email
- password
- optional full name

Expected product behavior:

- create independent learner account
- create personal tenant automatically
- assign role `independent_learner`
- send email verification

Current repo behavior:

- implemented in backend
- personal tenant auto-creation exists in `AuthService`
- frontend registration currently sends only `email`, `password`, `invite_token`

### 2. Login

User signs in using:

- email
- password
- optional tenant context

Independent learner behavior:

- tenant context can be omitted
- backend infers tenant if the email belongs to exactly one `independent_learner` account

Expected result:

- issue access token
- issue refresh token
- redirect to independent learner workspace
- if profile incomplete, redirect to profile completion

### 3. Choose Goal

User views available learning goals and selects one.

Expected result:

- goal becomes the context for diagnostic selection
- next action is to start a diagnostic session

Dependency:

- the learner tenant must have goals available

### 4. Start Diagnostic

Platform creates or resumes an open diagnostic session tied to:

- user
- goal
- tenant

Expected result:

- create `diagnostic_tests` row if none open
- return `test_id`
- open adaptive diagnostic page

### 5. Answer Questions

For each step:

- frontend fetches next question
- learner submits answer
- system scores answer
- state is persisted
- next question is selected adaptively

### 6. Submit Test

When adaptive engine is done or question limit is reached:

- diagnostic is finalized
- topic scores are calculated
- weak topics are detected
- roadmap generation is requested

### 7. Weak Topic Detection

System converts answer-level performance into topic-level weakness signals.

Outputs:

- topic scores
- weak topic list
- weakness clusters
- prerequisite deficiency signals

### 8. Roadmap Generation

System:

- prioritizes weak topics
- expands prerequisites
- orders learning path
- generates roadmap steps with deadlines and difficulty

### 9. Dashboard View

User lands on dashboard showing:

- completion percentage
- weak areas
- roadmap status
- AI suggestions
- cognitive model
- retention and progress signals

### 10. Track Progress

User progresses through roadmap steps:

- pending
- in progress
- completed

Progress is reflected on:

- roadmap page
- dashboard
- progress page
- topic view

### 11. Complete Topics

Learner opens a topic page, studies explanations, sees knowledge graph reasoning, then marks the roadmap step completed.

Expected result:

- roadmap step status updates
- analytics refreshes
- dashboard signals change
- recommendations shift to next topic

---

## 2.2 Backend Flow by Stage

### Register Flow

`POST /auth/register`  
Route -> `AuthService.register()` -> `TenantRepository` + `UserRepository` + `UserTenantRoleRepository` -> PostgreSQL

Detailed flow:

1. Validate password strength
2. Resolve role as `independent_learner` by default
3. If tenant not supplied and role is `independent_learner`, create personal tenant
4. Validate tenant exists
5. Create user row
6. Create tenant-role membership
7. Create verification token
8. Commit transaction
9. Queue verification email

### Login Flow

`POST /auth/login`  
Route -> `AuthService.login()` -> `UserRepository` + session/token services -> PostgreSQL

Detailed flow:

1. Resolve tenant using tenant ID, subdomain, host, or independent learner email inference
2. Load user scoped to tenant
3. Verify password
4. Enforce lock/MFA/session policies
5. Create access token and refresh token
6. Persist active session
7. Return authenticated response

### Goal Selection Flow

`GET /goals`  
Route -> `GoalService.list_goals_page()` -> `GoalRepository.list_all()` -> PostgreSQL

### Diagnostic Start Flow

`POST /diagnostic/start`  
Route -> `DiagnosticService.start_test()` -> `GoalRepository` + `DiagnosticRepository` -> PostgreSQL

Detailed flow:

1. Validate goal belongs to tenant
2. Check for existing open diagnostic for user + goal + tenant
3. Reuse open test if present
4. Otherwise create test row
5. Commit

### Question Answer Flow

`POST /diagnostic/answer`  
Route -> `DiagnosticService.answer_question()` -> `TopicRepository` + `DiagnosticRepository` + adaptive logic -> PostgreSQL

Detailed flow:

1. Lock diagnostic row
2. Validate test ownership and status
3. Validate submitted question is the expected next question
4. Load question content
5. Score answer
6. Upsert `user_answers`
7. Update persisted diagnostic state
8. Emit learning-related side effects
9. Commit

### Diagnostic Submit Flow

`POST /diagnostic/submit`  
Route -> `DiagnosticService.finalize_test()` -> `RoadmapService.ensure_generation_requested()` -> `OutboxService` -> PostgreSQL

Detailed flow:

1. Finalize diagnostic
2. Compute result summary and topic scores
3. Request roadmap generation
4. Insert outbox event for async-safe roadmap generation
5. Commit

### Roadmap Generation Flow

`POST /roadmap/generate`  
Route -> `RoadmapService.ensure_generation_requested()` -> `RoadmapService.generate()` -> repositories + engines -> PostgreSQL

Detailed flow:

1. Load or create roadmap identity for user + goal + test
2. Read topic scores from diagnostic
3. Load prerequisite graph
4. Build learning profile
5. Run recommendation engine
6. Expand prerequisite paths
7. Generate ordered steps
8. Persist roadmap and steps
9. Mark roadmap `ready`
10. Emit domain events, notifications, analytics refresh tasks
11. Commit

### Dashboard Flow

`GET /dashboard/student`  
Route -> `DashboardService.student_dashboard()` -> `LearningIntelligenceService.student_dashboard()` -> repositories/queries -> PostgreSQL

This route is reused for both:

- `student`
- `independent_learner`

### Progress Update Flow

`PATCH /roadmap/steps/{step_id}`  
Route -> `RoadmapService.update_step_status()` -> `RoadmapRepository` -> PostgreSQL

Current limitation:

- route currently allows only `student`, not `independent_learner`
- this is a real implementation bug for this panel

---

## 2.3 Database Flow by Stage

### Registration

- insert into `tenants`
- insert into `users`
- insert into `user_tenant_roles`
- insert verification/session-related rows through auth subsystems

### Goal Selection

- read from `goals`
- optionally read from `goal_topics`

### Diagnostic Lifecycle

- insert into `diagnostic_tests`
- read from `questions`
- insert/update `user_answers`
- insert/update diagnostic state support tables
- update per-topic mastery signals through downstream services

### Roadmap Lifecycle

- read diagnostic topic scores
- read `topics`
- read `topic_prerequisites`
- insert into `roadmaps`
- insert into `roadmap_steps`

### Progress Lifecycle

- update `roadmap_steps.progress_status`
- read analytics and topic mastery projections
- refresh downstream summary signals

---

## 3. UI Structure

## 3.1 Page Map

Recommended Independent Learner Panel pages:

- Landing Page
- Registration/Login
- Goal Selection Page
- Diagnostic Test Page
- Diagnostic Result Page
- Dashboard
- Roadmap View
- Topic Learning Page
- Progress Tracker

Current repo reality:

- registration/login exists via shared `/auth`
- independent learner routes exist under `/independent-learner/*`
- most independent learner pages re-export shared student pages

## 3.2 Landing Page

### Purpose

Introduce the B2C/self-serve value proposition and push users into registration.

### Components

- hero section
- value proposition cards
- how it works timeline
- testimonials/social proof
- pricing or trial CTA
- FAQ
- register/login CTA

### Data Required

- mostly static marketing content
- optional feature flags
- optional pricing plan data

### API Calls

- none required for static version
- optional pricing/subscription endpoint in future

### Current Status

- generic landing page components exist
- not a dedicated independent-learner-specific product landing flow yet

## 3.3 Registration/Login

### Components

- email input
- password input
- tenant/workspace input for login
- MFA input
- mode switcher: login/register/reset/verify
- success/error messaging

### Data Required

- email
- password
- tenant context for institutional users
- optional verification token/reset token

### API Calls

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/email-verification`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`

### Current Status

- implemented
- UI explicitly says independent learners can leave tenant field blank on login

## 3.4 Goal Selection Page

### Components

- goal list cards
- goal description
- selected goal state
- start diagnostic CTA

### Data Required

- goal ID
- goal name
- goal description

### API Calls

- `GET /goals`
- `POST /diagnostic/start`

### Current Status

- implemented
- shared student page reused by independent learner route

## 3.5 Diagnostic Test Page

### Components

- current question card
- answer options or textarea
- progress bar
- answered count
- continue/submit CTA
- error state

### Data Required

- `test_id`
- `goal_id`
- question payload
- difficulty label
- question type
- answer options

### API Calls

- `GET /diagnostic/{test_id}`
- `GET /diagnostic/next/{test_id}`
- `POST /diagnostic/answer`
- `POST /diagnostic/submit`

### Current Status

- implemented
- adaptive sequence is driven by backend

## 3.6 Diagnostic Result Page

### Components

- topic score summary
- weak topics
- prerequisite gaps
- roadmap generation status
- CTA to roadmap/dashboard

### Data Required

- topic scores
- weak topics
- roadmap status
- learning profile summary

### API Calls

- `GET /diagnostic/result?test_id=...`
- `POST /roadmap/generate` for retry/failure case

### Current Status

- implemented through shared learner page

## 3.7 Dashboard

### Components

- KPI cards
- progress distribution chart
- recommendation panel
- activity feed
- cognitive model card
- retention review card
- weak topic panel
- mentor suggestions

### Data Required

- completion percent
- total/completed/in-progress steps
- weak topics
- mentor suggestions
- recent activity
- retention stats
- leaderboard/gamification
- roadmap snapshot

### API Calls

- `GET /dashboard/student`
- `GET /roadmap/{user_id}`
- `GET /topics`

### Current Status

- implemented
- same backend dashboard endpoint serves students and independent learners

## 3.8 Roadmap View

### Components

- roadmap hero summary
- step cards
- step status pills
- start/complete/reopen actions
- roadmap flow visualization
- topic CTA
- mentor CTA

### Data Required

- roadmap ID
- roadmap status
- roadmap steps
- topic names
- step rationale
- progress status

### API Calls

- `GET /roadmap/{user_id}` or `GET /roadmap/view`
- `PATCH /roadmap/steps/{step_id}`

### Current Status

- UI implemented
- patch route currently blocks `independent_learner`

## 3.9 Topic Learning Page

### Components

- topic explanation
- examples
- practice questions
- knowledge graph visualization
- dependency chain
- next recommended topics
- roadmap status action

### Data Required

- topic detail
- knowledge graph nodes/edges
- topic reasoning
- roadmap step for topic

### API Calls

- `GET /topics/{topic_id}`
- `GET /topics/graph`
- `GET /topics/reasoning/{topic_id}`
- `GET /roadmap/{user_id}`
- `PATCH /roadmap/steps/{step_id}`

### Current Status

- implemented on learner side
- independent learner alias route exists
- same roadmap patch restriction applies

## 3.10 Progress Tracker

### Components

- completion KPI cards
- progress timeline
- mastery pie chart
- weak topic story
- recommendation panel
- activity feed

### Data Required

- roadmap progress
- weak topics
- activity history
- mentor suggestions

### API Calls

- `GET /dashboard/student`
- `GET /roadmap/{user_id}`

### Current Status

- implemented through shared learner page

---

## 4. Dashboard Breakdown

## 4.1 Primary Dashboard Objectives

The dashboard should answer:

- How much have I completed?
- Where am I weak?
- What should I do next?
- What topics are already done?
- Which topics are pending or blocked?
- How is my learning momentum changing?

## 4.2 Core Metrics

### Progress Percentage

Definition:

- `completed_steps / total_steps * 100`

Source:

- `StudentDashboardResponse.completion_percent`
- roadmap progress block

### Weak Areas

Definition:

- topics with lowest mastery score
- usually score below threshold, currently weak topic UI uses `< 72`

Source:

- `weak_topic_heatmap`
- `weak_topics`
- `weakness_clusters`

### Completed Topics

Definition:

- roadmap steps with `progress_status = completed`

Source:

- roadmap steps
- dashboard roadmap progress summary

### Pending Topics

Definition:

- roadmap steps not yet completed

Source:

- roadmap steps

### Recommended Next Topics

Definition:

- mentor/recommendation output plus roadmap ordering and topic reasoning

Source:

- `mentor_suggestions`
- roadmap top pending steps
- topic reasoning recommendations

## 4.3 Recommended Widgets

- Completion KPI card
- In-progress KPI card
- Weak topics panel
- Recommended next actions panel
- Roadmap progress chart
- Retention review widget
- Recent activity feed
- Knowledge graph quick view
- Mentor suggestions panel

## 4.4 Charts

- Progress line chart
  - source: learning velocity / progress series
- Mastery distribution pie chart
  - source: completed vs in_progress vs pending roadmap steps
- Weak topic heatmap/bar chart
  - source: topic mastery scores
- Activity timeline
  - source: learning events

## 4.5 APIs Used

- `GET /dashboard/student`
- `GET /roadmap/{user_id}`
- `GET /topics`
- optional:
  - `GET /analytics/retention`
  - `GET /topics/graph`

---

## 5. Backend Architecture

## 5.1 Core API Map

### Auth

#### `POST /auth/register`

- Route: `auth_routes.register`
- Service: `AuthService.register`
- Engine/Rules: password validation, auth rules
- Repository: `TenantRepository`, `UserRepository`, `UserTenantRoleRepository`
- DB: `tenants`, `users`, membership/auth tables

#### `POST /auth/login`

- Route: `auth_routes.login`
- Service: `AuthService.login`
- Engine/Rules: auth rules, token/session logic
- Repository: `UserRepository`, `SessionRepository`, `RefreshTokenRepository`
- DB: `users`, sessions, refresh tokens

### Diagnostic

#### `POST /diagnostic/start`

- Route: `diagnostic_routes.start_diagnostic`
- Service: `DiagnosticService.start_test`
- Engine: none heavy here
- Repository: `GoalRepository`, `DiagnosticRepository`
- DB: `goals`, `diagnostic_tests`

#### `POST /diagnostic/submit`

- Route: `diagnostic_routes.submit_diagnostic`
- Service: `DiagnosticService.finalize_test`
- Engine: weakness/scoring logic path
- Repository: `DiagnosticRepository`
- DB: `diagnostic_tests`, `user_answers`, topic score projections

### Roadmap

#### `POST /roadmap/generate`

- Route: `roadmap_routes.generate_roadmap`
- Service: `RoadmapService.ensure_generation_requested` and `RoadmapService.generate`
- Engine:
  - `LearningProfileEngine`
  - `WeaknessModelingEngine`
  - `KnowledgeGraphEngine`
  - `RecommendationService`
  - `TopicDifficultyEngine`
- Repository:
  - `RoadmapRepository`
  - `DiagnosticRepository`
  - `TopicRepository`
- DB:
  - `diagnostic_tests`
  - topic score tables/projections
  - `topics`
  - `topic_prerequisites`
  - `roadmaps`
  - `roadmap_steps`

#### `GET /roadmap/view`

- Route: `roadmap_routes.view_current_user_roadmaps`
- Service: `RoadmapService.list_for_user_page`
- Repository: `RoadmapRepository`
- DB: `roadmaps`, `roadmap_steps`

## 5.2 Route -> Service -> Engine -> Repository -> DB

### Diagnostic Answer Example

`POST /diagnostic/answer`

1. Route validates request and auth
2. Service verifies ownership and question sequence
3. Domain scoring rules evaluate answer
4. Adaptive logic decides difficulty/next-step behavior
5. Repository upserts answer and state
6. DB persists test state and answer row

### Roadmap Generation Example

`POST /roadmap/generate`

1. Route checks auth and payload
2. Service loads diagnostic outputs
3. Engines compute:
   - learning profile
   - weakness clusters
   - recommendation targets
   - prerequisite learning paths
4. Repository writes roadmap and steps
5. DB stores final roadmap

---

## 6. Database Usage

## 6.1 Table Usage

### `users`

Used for:

- learner identity
- auth state
- role assignment
- profile completion
- gamification summary values

Independent learner specifics:

- role is `independent_learner`
- tenant points to a personal tenant

### `goals`

Used for:

- presenting available learning objectives
- scoping diagnostics
- scoping roadmap generation

Risk:

- goals are tenant-scoped, so personal tenants need seeded/copied goals or the panel becomes unusable

### `diagnostic_tests`

Used for:

- one diagnostic session per learner/goal cycle
- lifecycle timestamps
- diagnostic ownership

### `user_answers`

Used for:

- storing answer text/choice
- score
- accuracy
- time taken
- attempt count

### `topics`

Used for:

- core knowledge graph nodes
- topic display
- roadmap step references
- topic learning page content

### `topic_prerequisites`

Used for:

- prerequisite edges
- dependency tracing
- learning path construction
- weakness foundation detection

### `roadmaps`

Used for:

- generated plan identity for one user + goal + diagnostic
- roadmap status:
  - generating
  - ready
  - failed

### `roadmap_steps`

Used for:

- ordered learning tasks
- topic references
- estimated hours
- deadline
- progression status
- rationale

## 6.2 Data Flow Between Tables

### Registration Flow

`users` <- created after personal tenant resolution

### Diagnostic Flow

`goals` -> `diagnostic_tests` -> `user_answers`

### Knowledge Graph Flow

`topics` + `topic_prerequisites` -> weakness detection and roadmap generation

### Roadmap Flow

`diagnostic_tests` + topic score outputs + `topics` + `topic_prerequisites` -> `roadmaps` -> `roadmap_steps`

### Progress Flow

`roadmap_steps.progress_status` updates -> dashboard/progress analytics

---

## 7. Core Logic

## 7.1 Diagnostic Scoring Logic

Current scoring logic is simple and deterministic.

Behavior:

- normalize answer
- normalize correct answer
- normalize accepted aliases
- if learner answer matches any valid normalized answer, score `100`
- else score `0`
- accuracy = `score / 100`

Strengths:

- explainable
- easy to test
- reliable for MCQ and alias-driven short answers

Limitations:

- no partial credit
- no semantic matching
- weak for long-form answers

## 7.2 Weak Topic Detection

Current logic combines:

- low topic score
- weak prerequisites
- confidence
- retention score

Outputs:

- deep weaknesses
- weakness clusters

Current thresholds in practice:

- weak topic UI commonly filters below about `72`
- missing foundation checks commonly use below `70`

Severity depends on:

- mastery gap
- number of missing weak prerequisites
- confidence signal
- retention decay

## 7.3 Prerequisite Tracing

Current logic uses graph traversal over `topic_prerequisites`.

Capabilities:

- fetch all prerequisites for a topic
- calculate dependency depth
- generate prerequisite-first learning path
- detect circular dependencies

Used in:

- roadmap generation
- topic reasoning
- missing foundation detection

## 7.4 Roadmap Generation Logic

Current generation logic:

1. load topic scores from diagnostic
2. load prerequisite graph
3. infer learner profile from timing and accuracy
4. rank weak topics through recommendation service
5. add cluster-related weak topics
6. expand prerequisite learning paths
7. sort into topic order
8. calculate dependency depths
9. generate steps with:
   - priority
   - estimated time
   - difficulty
   - deadline
   - rationale
10. persist roadmap

Roadmap timing logic varies by profile:

- `slow_deep_learner`: longer step windows
- `practice_focused`: shorter windows
- `concept_focused`: moderate expansion

---

## 8. Testing

## 8.1 Existing Repo Coverage

The repo already contains meaningful relevant tests, including:

- `backend/tests/test_diagnostic_scoring.py`
- `backend/tests/test_recommendation_service.py`
- `backend/tests/test_roadmap_generation.py`
- `backend/tests/test_service_integration_flow.py`
- `backend/tests/test_auth_route_contracts.py`
- `backend/tests/test_diagnostic_routes.py`
- `backend/tests/test_roadmap_routes.py`
- `learning-platform-frontend/tests/e2e/learner-journey.spec.ts`

This is a strong base, but the independent learner panel still needs panel-specific coverage.

## 8.2 Unit Tests

### Diagnostic Scoring Tests

Required cases:

- correct exact answer -> score 100
- accepted alias answer -> score 100
- wrong answer -> score 0
- normalization works across case/punctuation
- blank answer -> score 0

Existing evidence:

- alias and rejection tests are present

### Recommendation Logic Tests

Required cases:

- weak topics prioritized over strong topics
- prerequisites inserted before dependent weak topics
- ML async fallback returns rule-engine path when AI is not ready
- recommendation explanation payload is populated

Existing evidence:

- explainable priority test present
- async fallback test present
- foundation ordering test present

## 8.3 API Tests

### Register/Login

Cases:

- register independent learner without tenant ID
- verify personal tenant is created
- login without tenant context
- login with wrong password
- login blocked when email not verified
- login requires profile completion flow when profile incomplete

### Diagnostic Submit

Cases:

- start diagnostic with valid goal
- answer valid next question
- reject answer to unexpected question
- submit completed diagnostic
- reject submit for unauthorized test

### Roadmap Generate

Cases:

- generate roadmap from valid completed diagnostic
- return existing ready roadmap
- mark failed if generation errors
- verify step ordering respects prerequisites

## 8.4 Integration Tests

### Full Flow Test

Critical end-to-end path:

1. register independent learner
2. verify email
3. login without tenant context
4. complete profile
5. load goals
6. start diagnostic
7. answer sequence
8. submit diagnostic
9. generate roadmap
10. load dashboard
11. update step progress

Current repo coverage:

- service integration flow exists
- frontend learner journey exists

Missing independent-learner-specific integration:

- route path assertions under `/independent-learner/*`
- personal-tenant goal availability
- independent learner progress patch authorization

## 8.5 Edge Cases

- no goals available in personal tenant
- duplicate registration email
- login with ambiguous tenant context
- diagnostic resumed after interruption
- question deleted after test started
- roadmap generation fails midway
- no weak topics detected
- prerequisite graph contains cycle
- independent learner tries to mark roadmap step complete and receives 403

---

## 9. Current Status Audit

## 9.1 Completed

- Auth registration and login are production-oriented and fairly mature.
- Independent learner personal-tenant auto-creation is implemented in backend auth service.
- Tenant inference on login for independent learners is implemented.
- Shared learner flow exists for goals, diagnostic, diagnostic result, roadmap, dashboard, topic page, and progress page.
- Dashboard API supports both `student` and `independent_learner`.
- Diagnostic engine, weakness modeling, recommendation service, and roadmap generation are implemented.
- There is meaningful backend and frontend automated test coverage.

## 9.2 Partially Working

- Independent learner frontend exists, but most pages are route aliases to the student experience rather than a deeply specialized panel.
- Personal workspaces are created, but content/goals are still tenant-scoped, so self-serve onboarding depends on tenant content availability.
- Roadmap generation lifecycle exists, including generating/ready/failed states, but failure recovery is still mostly operational rather than productized.
- Topic learning, mentor, and progress experiences are available, but they are generalized learner pages, not specifically tuned for independent learners.

## 9.3 Missing or Weak

- No clear default content provisioning flow for a newly created personal tenant.
- No dedicated B2C onboarding pipeline that seeds goals/topics/resources into independent learner personal workspaces.
- No true independent-learner-specific backend dashboard or recommendation strategy.
- No clear subscription/billing/product packaging logic for B2C independent learners in the inspected scope.
- No panel-specific analytics or conversion funnel instrumentation described for self-serve onboarding.

---

## 10. Critical Issues

## 10.1 Breaking Bugs

### 1. Independent learners cannot update roadmap step progress

Current code in `roadmap_routes.py` only allows:

- `student`

This blocks:

- `PATCH /roadmap/steps/{step_id}`
- effective progress tracking for independent learners
- topic completion flows
- roadmap interaction from the independent learner panel

Impact:

- major functional break in core panel journey

### 2. Independent learners cannot trigger adaptive roadmap refresh

`POST /roadmap/adaptive-refresh` also only allows `student`.

Impact:

- personalization refresh is blocked for the panel

### 3. Personal tenant may have zero goals

Registration creates a personal tenant, but inspected code does not seed or copy goals into that tenant.

Since goals are tenant-scoped:

- `GET /goals` may return empty
- learner cannot start diagnostic
- full panel flow can dead-end immediately after onboarding

Impact:

- high severity onboarding failure risk

## 10.2 Logic Errors

### 4. Independent learner panel is presented as distinct, but core backend is shared

This is not itself wrong, but if product expects different business logic from student panel, the current implementation does not provide that separation.

### 5. Registration frontend does not currently send richer learner profile data

Backend supports `full_name`; current frontend registration sends minimal payload.

Impact:

- weaker personalization at onboarding
- poorer workspace naming/user experience

## 10.3 Missing Validations

- no evident panel-specific validation that a personal tenant is content-ready before redirecting learner into the goal flow
- no explicit guard ensuring an independent learner always has at least one usable goal
- no explicit product state for “workspace provisioned but content still syncing”

## 10.4 Scalability Risks

- tenant-scoped duplication of goals/topics for every personal tenant can become expensive at scale if implemented naively
- learner dashboard appears to aggregate multiple signals synchronously, which may become heavy for high-cardinality users or tenants
- roadmap generation currently commits many side effects around the same flow; this is correct functionally, but operational complexity increases under load

---

## 11. Performance and Scalability

## 11.1 Database Optimization

Recommendations:

- index hot filters:
  - `users(tenant_id, email)`
  - `diagnostic_tests(user_id, goal_id, completed_at)`
  - `user_answers(test_id, question_id)`
  - `roadmaps(user_id, goal_id, test_id, status)`
  - `roadmap_steps(roadmap_id, progress_status, priority)`
  - `topics(tenant_id, id)`
  - `topic_prerequisites(topic_id, prerequisite_topic_id)`

- keep topic score projections/materialized summaries for dashboard reads
- avoid duplicating full content into every personal tenant unless necessary
- prefer shared catalog + tenant visibility mapping for B2C scale

## 11.2 API Optimization

- use async-safe precomputed snapshots for dashboard-heavy panels
- cache topic graph reads
- avoid regenerating roadmap synchronously on every page load
- poll only while roadmap status is `generating`

Current repo positives:

- async stack
- cached/polling patterns exist
- precomputed analytics service exists

## 11.3 Async Improvements

- move post-roadmap side effects fully behind outbox/job workers where possible
- precompute learner dashboard summary after diagnostic completion and roadmap updates
- add background provisioning workflow for personal tenant content seeding

---

## 12. Security

## 12.1 JWT Usage

Strengths:

- access tokens decoded with tenant and session context
- refresh sessions are persisted
- session revocation and blacklist checks exist
- scope-aware auth exists

Checks:

- ensure short access token TTL
- ensure refresh rotation is enforced consistently
- ensure tenant and role claims are always validated server-side

## 12.2 Password Hashing

Strengths:

- password hashing exists in auth service
- password strength validation exists before user creation

Need to keep:

- strong bcrypt/argon policy
- breached-password screening if platform grows

## 12.3 Access Control

Strengths:

- route-level role guards exist
- profile completion and email verification guards exist
- tenant scoping is built into repositories and auth context

Weakness discovered:

- roadmap progress write actions exclude `independent_learner`

## 12.4 Multi-Tenant Isolation

Good signs:

- tenant-aware repositories
- tenant role membership model
- partial RLS rollout and tests

Remaining need:

- full coverage validation for all learner-critical tables in production

---

## 13. Enhancements

## 13.1 Short-Term Improvements

- allow `independent_learner` on roadmap step updates and adaptive refresh
- provision default goals/topics/resources for personal tenants
- add explicit onboarding state: workspace setup, profile completion, choose goal
- add B2C-specific dashboard copy and empty states
- send `full_name` during registration and use it for workspace naming
- add independent-learner-specific end-to-end tests

## 13.2 Advanced Features

- adaptive testing with confidence-based early stop
- AI-generated next best topic explanations
- AI learning coach that explains why a topic is next
- gamified study quests and streak recovery workflows
- spaced repetition engine tied to roadmap status
- goal templates:
  - data science
  - web development
  - exam prep
  - job transition
- personal knowledge journal
- subscription tiers:
  - free
  - pro
  - mentor-assisted

## 13.3 Product-Led Growth Features

- one-click “start with a recommended goal”
- trial roadmap preview before full signup
- shareable progress cards
- habit nudges via email/push
- reactivation flows for dormant learners

---

## 14. Final Implementation Checklist

## Backend

- support `independent_learner` in roadmap step update routes
- support `independent_learner` in adaptive roadmap refresh route
- seed or map goals for personal tenants
- confirm personal tenant content model
- add panel-specific integration tests
- verify tenant isolation on all learner-facing tables
- ensure dashboard projections remain performant

## Frontend

- create a true independent learner landing/onboarding experience
- keep shared learner pages where useful, but add independent-learner-specific copy and states
- add personal workspace setup status UI
- surface “no goals available” as actionable onboarding state
- validate progress actions after route guard fix

## Testing

- unit test role-specific roadmap progress authorization
- integration test personal-tenant onboarding
- API test empty-goal scenario
- end-to-end test independent learner route flow under `/independent-learner/*`
- regression test diagnostic -> roadmap -> progress update

## Deployment

- run migrations for all learner-critical tables
- verify email delivery and verification links
- verify session cookies and JWT settings per environment
- confirm background workers and outbox consumers are active
- monitor roadmap generation failures and dashboard latency
- add alerts for onboarding failures in personal tenants

---

## Final Assessment

The Independent Learner Panel has a strong underlying learner engine already available in the current codebase. Auth, diagnostic, weakness detection, roadmap generation, dashboarding, and topic learning all exist in usable form. The panel is not starting from zero.

However, it is not yet fully production-ready as a standalone B2C panel.

The biggest blockers are:

- independent learners cannot update roadmap progress because of route-level role restrictions
- personal tenants are created without a visible guaranteed content provisioning flow
- the panel is mostly a role/routing wrapper on top of shared student flows rather than a fully differentiated self-serve product experience

If those gaps are fixed, this panel can move from “shared learner capability” to a true independent learner SaaS experience.
