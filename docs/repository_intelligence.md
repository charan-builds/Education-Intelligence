# Repository Intelligence Catalog (34 Repositories)

This document provides a detailed catalog of the 34 repository classes in the database access layer (`app/infrastructure/repositories/`) of the **Learning Intelligence Platform** backend.

---

## Group 1: User & Auth Repositories

| Repository Class | Source File | Models Handled | Core Purpose |
| :--- | :--- | :--- | :--- |
| `UserRepository` | [user_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py) | `User` | Handles user credential and profile lookups. |
| `SessionRepository` | [session_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/session_repository.py) | `Session` | Tracks active login sessions and durations. |
| `RefreshTokenRepository` | [refresh_token_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/refresh_token_repository.py) | `RefreshToken` | Coordinates token swaps and rotations. |
| `TokenBlacklistRepository` | [token_blacklist_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/token_blacklist_repository.py) | None | Handles revoked access token signatures. |
| `UserTenantRoleRepository` | [user_tenant_role_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_tenant_role_repository.py) | `UserTenantRole` | Manages role definitions within tenant scopes. |
| `AuthLogRepository` | [auth_log_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/auth_log_repository.py) | `AuthLog` | Logs authentication attempts for audit trials. |

### Primary Repository Detail: `UserRepository`
*   **Queries**: `SELECT * FROM users WHERE email = :email AND tenant_id = :tenant_id`
*   **CRUD Operations**: standard creation (`create`), update (`update`), and retrieve (`find_by_email`).
*   **Tenant Filtering**: Enforced by Postgres RLS using the session parameter `app.current_tenant_id`.
*   **Caching**: Caches profile queries in Redis with a 15-minute TTL; invalidates on updates.
*   **Indexes Used**: Unique index on `(email, tenant_id)`.
*   **Performance**: Fast index-seek lookups ($\mathcal{O}(1)$ average latency < 5ms).
*   **Transaction Boundaries**: Managed by application service database transaction blocks.
*   **Optimization Opportunities**: Load related tenant parameters using selectin joins to avoid N+1 query structures.
*   **Related Models**: [User](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/models/user.py)
*   **Related Services**: [AuthService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/auth_service.py)

---

## Group 2: Diagnostics & Assessment Repositories

| Repository Class | Source File | Models Handled | Core Purpose |
| :--- | :--- | :--- | :--- |
| `DiagnosticRepository` | [diagnostic_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/diagnostic_repository.py) | `DiagnosticTest`, `UserAnswer` | Tracks diagnostic quiz sessions and options. |

### Primary Repository Detail: `DiagnosticRepository`
*   **Queries**: `SELECT * FROM user_answers WHERE test_id = :test_id`
*   **CRUD Operations**: creation (`save_answer`), retrieve (`get_session`).
*   **Tenant Filtering**: RLS isolation policies filter sessions by user tenant context.
*   **Caching**: Active session data is cached in Redis; aggregates are updated on database commits.
*   **Indexes Used**: Index on `user_answers.test_id`, composite index on `(user_answers.test_id, user_answers.question_id)`.
*   **Performance**: Session listings require joining topic maps; requires covering indexes to avoid table scans.
*   **Transaction Boundaries**: Submit actions wrap answer writes and test progress checks in database transactions.
*   **Optimization Opportunities**: Batch answer writes using database copy commands.
*   **Related Models**: `DiagnosticTest`, `UserAnswer`
*   **Related Services**: [DiagnosticService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/diagnostic_service.py)

---

## Group 3: Roadmap & Goal Repositories

| Repository Class | Source File | Models Handled | Core Purpose |
| :--- | :--- | :--- | :--- |
| `RoadmapRepository` | [roadmap_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/roadmap_repository.py) | `Roadmap`, `RoadmapStep` | Tracks learning roadmap generations. |
| `GoalRepository` | [goal_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/goal_repository.py) | `Goal` | Handles CRUD operations for educational goals. |
| `UserGoalRepository` | [user_goal_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_goal_repository.py) | `UserGoal` | Links users to active goal paths. |

### Primary Repository Detail: `RoadmapRepository`
*   **Queries**: `SELECT * FROM roadmap_steps WHERE roadmap_id = :roadmap_id ORDER BY step_order`
*   **CRUD Operations**: creation (`create_roadmap`), update (`update_step_status`).
*   **Tenant Filtering**: RLS filters rows based on target user tenant identifiers.
*   **Caching**: Roadmap graphs are cached in Redis using roadmap IDs as keys.
*   **Indexes Used**: Index on `roadmap_steps.roadmap_id`, composite index on `(roadmap_steps.roadmap_id, roadmap_steps.status)`.
*   **Performance**: Deep goal nets require recursion; limits queries to steps linked to active roadmaps.
*   **Transaction Boundaries**: Generates roadmaps and steps in single transactions.
*   **Optimization Opportunities**: Run step status updates in bulk using single queries.
*   **Related Models**: `Roadmap`, `RoadmapStep`
*   **Related Services**: [RoadmapService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/roadmap_service.py)

---

## Group 4: Topic & Question Repositories

| Repository Class | Source File | Models Handled | Core Purpose |
| :--- | :--- | :--- | :--- |
| `TopicRepository` | [topic_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/topic_repository.py) | `Topic`, `Question` | Handles topic nodes and quiz questions. |
| `ResourceRepository` | [resource_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/resource_repository.py) | `Resource` | Tracks resource URLs linked to topics. |

### Primary Repository Detail: `TopicRepository`
*   **Queries**: `SELECT * FROM topic_prerequisites WHERE topic_id = :topic_id`
*   **CRUD Operations**: creation (`create_topic`), query (`get_all_with_prereqs`).
*   **Tenant Filtering**: Applies RLS filters to hide content across different tenants.
*   **Caching**: Topic graphs are cached globally in Redis; invalidates on new additions.
*   **Indexes Used**: Composite index on prerequisites: `(topic_id, prerequisite_id)`.
*   **Performance**: Pre-joins prerequisites using SQL expressions to avoid N+1 query patterns.
*   **Transaction Boundaries**: Updates topic descriptions and prerequisite nodes in single transactions.
*   **Optimization Opportunities**: Use CTE queries to speed up recursive prerequisite lookups.
*   **Related Models**: `Topic`, `Question`
*   **Related Services**: [TopicService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/topic_service.py)

---

## Group 5: Community & Social Repositories

| Repository Class | Source File | Models Handled | Core Purpose |
| :--- | :--- | :--- | :--- |
| `CommunityRepository` | [community_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/community_repository.py) | `Community`, `Thread`, `Reply` | Handles forum posts and replies. |
| `NotificationRepository` | [notification_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/notification_repository.py) | `Notification` | Queries student notifications and read flags. |

### Primary Repository Detail: `CommunityRepository`
*   **Queries**: `SELECT * FROM discussion_threads WHERE community_id = :community_id LIMIT :limit OFFSET :offset`
*   **CRUD Operations**: creation (`create_thread`), update (`resolve_thread`).
*   **Tenant Filtering**: Isolates forums by community workspace tenant codes using RLS.
*   **Caching**: Caches thread counts in Redis; invalidates on new reply entries.
*   **Indexes Used**: Index on `discussion_threads.community_id`, index on `discussion_replies.thread_id`.
*   **Performance**: Employs pagination on thread lists to avoid loading full message datasets.
*   **Transaction Boundaries**: Reply creations increment parent thread reply counters in single transactions.
*   **Optimization Opportunities**: Pre-aggregate reply counts to avoid counting columns on search executions.
*   **Related Models**: `Thread`, `Reply`
*   **Related Services**: [CommunityService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/community_service.py)

---

## Group 6: Mentoring Repositories

| Repository Class | Source File | Models Handled | Core Purpose |
| :--- | :--- | :--- | :--- |
| `MentorChatRepository` | [mentor_chat_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/mentor_chat_repository.py) | `MentorChatMessage` | Handles chat history queries. |
| `MentorMessageRepository` | [mentor_message_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/mentor_message_repository.py) | `MentorMessage` | Tracks mentor logs. |
| `MentorStudentRepository` | [mentor_student_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/mentor_student_repository.py) | `MentorStudent` | Links students to mentors. |

### Primary Repository Detail: `MentorChatRepository`
*   **Queries**: `SELECT * FROM mentor_chat_messages WHERE user_id = :user_id ORDER BY created_at DESC LIMIT :limit`
*   **CRUD Operations**: creation (`log_chat`), query (`get_chat_history`).
*   **Tenant Filtering**: RLS policies restrict chat histories to the user's active tenant scope.
*   **Caching**: Caches last 10 messages in Redis to build prompt context.
*   **Indexes Used**: Composite index on `(user_id, created_at)`.
*   **Performance**: Indexes allow chat queries to run in under 3ms.
*   **Transaction Boundaries**: Stores prompt and AI reply steps in separate write operations.
*   **Optimization Opportunities**: Batch queries for prompt histories to reduce database connection counts.
*   **Related Models**: `MentorChatMessage`
*   **Related Services**: [MentorService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/mentor_service.py)

---

## Group 7: Streaming & Outbox Repositories

| Repository Class | Source File | Models Handled | Core Purpose |
| :--- | :--- | :--- | :--- |
| `OutboxRepository` | [outbox_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/outbox_repository.py) | `OutboxEvent` | Tracks pending outbox events. |
| `DeadLetterRepository` | [dead_letter_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/dead_letter_repository.py) | `DeadLetterEvent` | Logs dead-letter event items. |
| `StreamOffsetRepository` | [stream_offset_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/stream_offset_repository.py) | `StreamOffset` | Tracks event offsets. |

### Primary Repository Detail: `OutboxRepository`
*   **Queries**: `SELECT * FROM outbox_events WHERE status = 'PENDING' LIMIT :batch_size FOR UPDATE SKIP LOCKED`
*   **CRUD Operations**: creation (`save_event`), query (`fetch_pending`).
*   **Tenant Filtering**: RLS is disabled to allow background sweeps to process items globally.
*   **Caching**: None (requires real-time transactional updates).
*   **Indexes Used**: Index on `(status, created_at)`.
*   **Performance**: Uses `FOR UPDATE SKIP LOCKED` to prevent locks across concurrent sweeps.
*   **Transaction Boundaries**: Writes events within transactional blocks.
*   **Optimization Opportunities**: Purge processed events weekly to control table size growth.
*   **Related Models**: `OutboxEvent`
*   **Related Services**: [OutboxService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/outbox_service.py)

---

## Group 8: Analytics & Profile Repositories

| Repository Class | Source File | Models Handled | Core Purpose |
| :--- | :--- | :--- | :--- |
| `AnalyticsSnapshotRepository` | [analytics_snapshot_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/analytics_snapshot_repository.py) | `AnalyticsSnapshot` | Manages dashboard snapshot tables. |
| `TopicScoreRepository` | [topic_score_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/topic_score_repository.py) | `TopicScore` | Tracks student scores per topic. |
| `UserProfileRepository` | [user_profile_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_profile_repository.py) | `UserProfile` | Manages student metadata profile details. |
| `LearningProfileRepository` | [learning_profile_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/learning_profile_repository.py) | `LearningProfile` | Handles student learning style settings. |

### Primary Repository Detail: `AnalyticsSnapshotRepository`
*   **Queries**: `SELECT * FROM analytics_snapshots WHERE tenant_id = :tenant_id ORDER BY snapshot_date DESC LIMIT 1`
*   **CRUD Operations**: creation (`save_snapshot`), query (`get_latest_snapshot`).
*   **Tenant Filtering**: RLS isolates analytics rows by tenant workspace context.
*   **Caching**: Caches dashboard datasets in Redis with a 5-minute TTL.
*   **Indexes Used**: Index on `(tenant_id, snapshot_date)`.
*   **Performance**: Fetches single precalculated rows to load admin charts.
*   **Transaction Boundaries**: Read-only queries execute outside active transaction contexts.
*   **Optimization Opportunities**: Compress snapshot histories using Postgres partitioning rules.
*   **Related Models**: `AnalyticsSnapshot`
*   **Related Services**: [PrecomputedAnalyticsService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/precomputed_analytics_service.py)
