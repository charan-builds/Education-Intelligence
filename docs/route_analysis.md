# Route Analysis Catalog (194 Endpoints)

This catalog analyzes all registered routes in the **Learning Intelligence Platform** backend. It is organized into 10 logical router modules representing the platform's API surface.

---

## Group 1: Authentication & Identity Router (21 Endpoints)

| Endpoint | Method | Authentication | Permissions | Endpoint Function | Database Tables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/auth/register` | `POST` | None | Public | `register` | `users`, `tenants`, `invites` |
| `/auth/login` | `POST` | None | Public | `login` | `users`, `sessions` |
| `/auth/logout` | `POST` | Access Token | Student/Admin | `logout` | `sessions` |
| `/auth/refresh` | `POST` | Refresh Token | Student/Admin | `refresh_session` | `sessions`, `users` |
| `/auth/invite-accept` | `POST` | None | Public | `accept_invite` | `users`, `invites` |
| `/auth/invites` | `POST` | Access Token | Admin | `create_invite` | `invites` |
| `/auth/send-otp` | `POST` | None | Public | `send_phone_otp` | `users` |
| `/auth/verify-otp` | `POST` | None | Public | `verify_phone_otp` | `users` |
| `/auth/mfa/setup` | `POST` | Access Token | Student/Admin | `setup_mfa` | `users` |
| `/auth/mfa/enable` | `POST` | Access Token | Student/Admin | `enable_mfa` | `users` |
| `/auth/mfa/disable` | `POST` | Access Token | Student/Admin | `disable_mfa` | `users` |
| `/auth/sessions` | `GET` | Access Token | Student/Admin | `list_active_sessions` | `sessions` |
| `/auth/logout-all` | `POST` | Access Token | Student/Admin | `logout_all_devices` | `sessions` |
| `/auth/email-verification/request` | `POST` | Access Token | Student | `request_email_verification` | `users` |
| `/auth/email-verification/confirm` | `POST` | None | Public | `confirm_email_verification` | `users` |
| `/auth/password-reset/request` | `POST` | None | Public | `request_password_reset` | `users` |
| `/auth/password-reset/confirm` | `POST` | None | Public | `confirm_password_reset` | `users` |
| `/auth/forgot-password` | `POST` | None | Public | `forgot_password` | `users` |
| `/auth/reset-password` | `POST` | None | Public | `reset_password_alias` | `users` |
| `/auth/verify-email` | `POST` | None | Public | `verify_email_alias` | `users` |
| `/auth/email-verification` | `POST` | None | Public | `confirm_email_verification_alias` | `users` |

### Primary Endpoint Detail: `POST /auth/login`
*   **Validation**: 5 requests/minute per IP rate limits.
*   **Services Called**: [AuthService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/auth_service.py)
*   **Repositories**: [UserRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
*   **Exceptions**: `HTTP 401 Unauthorized` (Invalid credentials).
*   **Performance Notes**: BCrypt verification is CPU-bound.
*   **Related Frontend Pages**: `/login` in [app/login/page.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/app/login/page.tsx)
*   **Related Tests**: [backend/tests/integration/test_auth.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_auth.py)
*   **Swagger Example**:
    ```json
    {
      "request": { "email": "user@tenant.com", "password": "SecurePassword123!" },
      "response": { "authenticated": true, "access_token": "token" }
    }
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        Client->>API: POST /auth/login
        API->>AuthService: login(email, password)
        AuthService->>UserRepository: find_by_email()
        UserRepository->>DB: SELECT FROM users
        AuthService-->>API: Token payload
        API-->>Client: JWT tokens
    ```

---

## Group 2: Diagnostic & Assessment Router (10 Endpoints)

| Endpoint | Method | Authentication | Permissions | Endpoint Function | Database Tables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/diagnostic/start` | `POST` | Access Token | Student | `start_diagnostic` | `diagnostic_tests`, `questions` |
| `/diagnostic` | `POST` | Access Token | Student | `start_diagnostic_alias` | `diagnostic_tests`, `questions` |
| `/diagnostic/submit` | `POST` | Access Token | Student | `submit_diagnostic` | `user_answers`, `diagnostic_tests` |
| `/diagnostic/complete` | `POST` | Access Token | Student | `submit_diagnostic_alias` | `user_answers`, `diagnostic_tests` |
| `/diagnostic/answer` | `POST` | Access Token | Student | `answer_diagnostic_question` | `user_answers` |
| `/diagnostic/next-question` | `POST` | Access Token | Student | `diagnostic_next_question` | `questions` |
| `/diagnostic/next/{test_id}` | `GET` | Access Token | Student | `diagnostic_next_question_for_test` | `questions` |
| `/diagnostic/result` | `GET` | Access Token | Student | `diagnostic_result` | `diagnostic_tests` |
| `/diagnostic/{test_id}` | `GET` | Access Token | Student | `get_diagnostic_session` | `diagnostic_tests` |
| `/diagnostic/{test_id}/gaps` | `GET` | Access Token | Student | `diagnostic_knowledge_gaps` | `topic_scores` |
| `/diagnostic/{test_id}/performance` | `GET` | Access Token | Student | `diagnostic_performance` | `topic_scores` |

### Primary Endpoint Detail: `POST /diagnostic/submit`
*   **Validation**: Time check limit validation.
*   **Services Called**: [DiagnosticService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/diagnostic_service.py)
*   **Repositories**: [DiagnosticRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/diagnostic_repository.py)
*   **Exceptions**: `HTTP 409 Conflict` (Timed out).
*   **Performance Notes**: Database row locks are used to prevent double submissions.
*   **Related Frontend Pages**: `/diagnostic` in [app/diagnostic/page.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/app/diagnostic/page.tsx)
*   **Related Tests**: [backend/tests/integration/test_diagnostic.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_diagnostic.py)
*   **Swagger Example**:
    ```json
    {
      "request": { "test_id": "uuid", "question_id": 1, "selected_option": 2, "time_taken": 10 },
      "response": { "score_updated": true, "completed": false }
    }
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        Client->>API: POST /diagnostic/submit
        API->>DiagnosticService: submit_answer()
        DiagnosticService->>DB: INSERT INTO user_answers
        DiagnosticService-->>API: Progress status
        API-->>Client: Result JSON
    ```

---

## Group 3: Learning Roadmap & Goals Router (13 Endpoints)

| Endpoint | Method | Authentication | Permissions | Endpoint Function | Database Tables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/roadmap` | `POST` | Access Token | Student | `generate_roadmap` | `roadmaps`, `roadmap_steps` |
| `/roadmap/generate` | `POST` | Access Token | Student | `generate_roadmap` | `roadmaps`, `roadmap_steps` |
| `/roadmap` | `GET` | Access Token | Student | `view_current_user_roadmaps` | `roadmaps` |
| `/roadmap/view` | `GET` | Access Token | Student | `view_current_user_roadmaps` | `roadmaps` |
| `/roadmap/adaptive-refresh` | `POST` | Access Token | Student | `adaptive_refresh_roadmap` | `roadmaps`, `roadmap_steps` |
| `/roadmap/steps/{step_id}` | `PATCH` | Access Token | Student | `update_roadmap_step` | `roadmap_steps` |
| `/roadmap/{user_id}` | `GET` | Access Token | Teacher/Admin | `list_roadmaps` | `roadmaps` |
| `/goals` | `GET` | Access Token | Student | `list_goals` | `goals` |
| `/goals` | `POST` | Access Token | Admin | `create_goal` | `goals` |
| `/goals/{goal_id}` | `PUT` | Access Token | Admin | `update_goal` | `goals` |
| `/goals/{goal_id}` | `DELETE` | Access Token | Admin | `delete_goal` | `goals` |
| `/goals/topics` | `GET` | Access Token | Student | `list_goal_topics` | `goal_topics` |
| `/goals/topics` | `POST` | Access Token | Admin | `create_goal_topic` | `goal_topics` |
| `/goals/topics/{link_id}` | `DELETE` | Access Token | Admin | `delete_goal_topic` | `goal_topics` |
| `/user/goals/current` | `GET` | Access Token | Student | `get_current_user_goal` | `user_goals` |
| `/user/goals/select` | `POST` | Access Token | Student | `select_user_goal` | `user_goals` |
| `/revision/today` | `GET` | Access Token | Student | `revision_today` | `roadmap_steps` |

### Primary Endpoint Detail: `POST /roadmap/generate`
*   **Validation**: Confirms completed diagnostics.
*   **Services Called**: [RoadmapService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/roadmap_service.py)
*   **Repositories**: [RoadmapRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/roadmap_repository.py)
*   **Exceptions**: `HTTP 400 Bad Request` (Diagnostics missing).
*   **Performance Notes**: Traverses Graph dependencies in-memory.
*   **Related Frontend Pages**: `/roadmap` in [app/roadmap/page.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/app/roadmap/page.tsx)
*   **Related Tests**: [backend/tests/integration/test_roadmap.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_roadmap.py)
*   **Swagger Example**:
    ```json
    {
      "request": { "goal_id": 12 },
      "response": { "roadmap_id": "uuid", "steps": [] }
    }
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        Client->>API: POST /roadmap/generate
        API->>RoadmapService: generate_roadmap_for_student()
        RoadmapService->>DB: INSERT INTO roadmaps
        RoadmapService-->>API: Generated steps
        API-->>Client: Roadmap JSON
    ```

---

## Group 4: Topic & Content Graph Router (20 Endpoints)

| Endpoint | Method | Authentication | Permissions | Endpoint Function | Database Tables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/topics` | `GET` | Access Token | Student | `list_topics` | `topics` |
| `/topics` | `POST` | Access Token | Admin | `create_topic` | `topics` |
| `/topics/{topic_id}` | `GET` | Access Token | Student | `get_topic` | `topics` |
| `/topics/{topic_id}` | `PUT` | Access Token | Admin | `update_topic` | `topics` |
| `/topics/{topic_id}` | `DELETE` | Access Token | Admin | `delete_topic` | `topics` |
| `/topics/graph` | `GET` | Access Token | Student | `get_topic_graph` | `topics`, `topic_prerequisites` |
| `/topics/prerequisites` | `GET` | Access Token | Student | `list_prerequisites` | `topic_prerequisites` |
| `/topics/prerequisites` | `POST` | Access Token | Admin | `create_prerequisite` | `topic_prerequisites` |
| `/topics/prerequisites/{prerequisite_id}` | `DELETE` | Access Token | Admin | `delete_prerequisite` | `topic_prerequisites` |
| `/topics/questions` | `GET` | Access Token | Student | `list_questions` | `questions` |
| `/topics/questions` | `POST` | Access Token | Admin | `create_question` | `questions` |
| `/topics/questions/{question_id}` | `PUT` | Access Token | Admin | `update_question` | `questions` |
| `/topics/questions/{question_id}` | `DELETE` | Access Token | Admin | `delete_question` | `questions` |
| `/topics/questions/ai-generate` | `POST` | Access Token | Admin | `generate_questions_with_ai` | `questions` |
| `/topics/questions/export` | `GET` | Access Token | Admin | `export_questions` | `questions` |
| `/topics/questions/export.csv` | `GET` | Access Token | Admin | `export_questions_csv` | `questions` |
| `/topics/questions/import` | `POST` | Access Token | Admin | `import_questions` | `questions` |
| `/topics/questions/import.csv` | `POST` | Access Token | Admin | `import_questions_csv` | `questions` |
| `/topics/reasoning/{topic_id}` | `GET` | Access Token | Student | `get_topic_reasoning` | `topic_scores` |
| `/topics/ai/explain` | `POST` | Access Token | Student | `explain_topic_with_ai` | `mentor_chat_messages` |

### Primary Endpoint Detail: `GET /topics/graph`
*   **Validation**: Confirms tenant scope.
*   **Services Called**: [TopicService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/topic_service.py)
*   **Repositories**: [TopicRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/topic_repository.py)
*   **Exceptions**: `HTTP 404 Not Found` (No topics defined).
*   **Performance Notes**: Cached in Redis with invalidation triggers when new topics are created.
*   **Related Frontend Pages**: `/topic` in [app/topic/page.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/app/topic/page.tsx)
*   **Related Tests**: [backend/tests/integration/test_topic.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_topic.py)
*   **Swagger Example**:
    ```json
    {
      "request": {},
      "response": { "nodes": [{"id": 1, "name": "Basic Programming"}], "edges": [] }
    }
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        Client->>API: GET /topics/graph
        API->>TopicService: get_topic_graph()
        TopicService->>Redis: Check Cache
        Redis-->>TopicService: Return Cached Graph JSON
        API-->>Client: Graph Nodes & Edges
    ```

---

## Group 5: Mentor AI & Guidance Router (12 Endpoints)

| Endpoint | Method | Authentication | Permissions | Endpoint Function | Database Tables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/mentor/chat` | `POST` | Access Token | Student | `mentor_chat` | `mentor_chat_messages` |
| `/mentor/chat/ack` | `POST` | Access Token | Student | `mentor_chat_ack` | `mentor_chat_messages` |
| `/mentor/chat/fallback` | `POST` | Access Token | Student | `mentor_chat_fallback` | `mentor_chat_messages` |
| `/mentor/chat/status/{request_id}` | `GET` | Access Token | Student | `mentor_chat_status` | `ai_requests` |
| `/mentor/agent/run` | `POST` | Access Token | Student | `mentor_agent_run` | `mentor_chat_messages` |
| `/mentor/agent/status` | `GET` | Access Token | Student | `mentor_agent_status` | `mentor_chat_messages` |
| `/mentor/hybrid-network` | `GET` | Access Token | Student | `hybrid_mentor_network` | `mentor_students` |
| `/mentor/hybrid-network/session-plan` | `POST` | Access Token | Student | `hybrid_mentor_session_plan` | `mentor_session_memories` |
| `/mentor/learners` | `GET` | Access Token | Teacher | `mentor_learners` | `mentor_students` |
| `/mentor/notifications` | `GET` | Access Token | Student | `mentor_notifications` | `notifications` |
| `/mentor/progress-analysis` | `GET` | Access Token | Student | `mentor_progress_analysis` | `analytics_snapshots` |
| `/mentor/suggestions` | `GET` | Access Token | Student | `mentor_suggestions` | `mentor_suggestions` |

### Primary Endpoint Detail: `POST /mentor/chat`
*   **Validation**: Message inputs are limited to 2000 characters.
*   **Services Called**: [MentorService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/mentor_service.py)
*   **Repositories**: [UserRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
*   **Exceptions**: `HTTP 422 Unprocessable Entity` (Input size validation error).
*   **Performance Notes**: Connects asynchronously to the AI microservice.
*   **Related Frontend Pages**: `/mentor` in [app/mentor/page.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/app/mentor/page.tsx)
*   **Related Tests**: [backend/tests/integration/test_mentor.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_mentor.py)
*   **Swagger Example**:
    ```json
    {
      "request": { "message": "Why is sorting useful?" },
      "response": { "reply": "Sorting structures data for faster lookup times." }
    }
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        Client->>API: POST /mentor/chat
        API->>MentorService: process_chat_message()
        MentorService->>AI_Client: post_query()
        AI_Client-->>MentorService: AI Response
        MentorService->>DB: INSERT INTO mentor_chat_messages
        MentorService-->>API: Message
        API-->>Client: Message JSON
    ```

---

## Group 6: Analytics & Operations Router (23 Endpoints)

| Endpoint | Method | Authentication | Permissions | Endpoint Function | Database Tables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/analytics/overview` | `GET` | Access Token | Teacher/Admin | `get_analytics_overview` | `analytics_snapshots` |
| `/analytics/platform-overview` | `GET` | Access Token | Super Admin | `get_platform_analytics_overview` | `analytics_snapshots` |
| `/analytics/precomputed/tenant-dashboard` | `GET` | Access Token | Teacher/Admin | `get_precomputed_tenant_dashboard` | `precomputed_analytics` |
| `/analytics/precomputed/user-learning-summary` | `GET` | Access Token | Student | `get_precomputed_user_learning_summary` | `precomputed_analytics` |
| `/analytics/precomputed/refresh` | `POST` | Access Token | Admin | `refresh_precomputed_analytics` | `precomputed_analytics` |
| `/analytics/learning-trends` | `GET` | Access Token | Teacher/Admin | `get_learning_trends` | `learning_events` |
| `/analytics/retention` | `GET` | Access Token | Teacher/Admin | `get_retention_analytics` | `topic_scores` |
| `/analytics/roadmap-progress` | `GET` | Access Token | Teacher/Admin | `get_roadmap_progress_analytics` | `roadmaps` |
| `/analytics/skill-vectors` | `GET` | Access Token | Teacher/Admin | `get_skill_vectors` | `user_skill_vectors` |
| `/analytics/student-insights` | `GET` | Access Token | Teacher/Admin | `get_student_insights` | `learning_events` |
| `/analytics/student/{user_id}` | `GET` | Access Token | Teacher/Admin | `get_student_performance_analytics` | `topic_scores` |
| `/analytics/topic-mastery` | `GET` | Access Token | Student | `get_topic_mastery_analytics` | `topic_scores` |
| `/analytics/topic/{topic_id}` | `GET` | Access Token | Teacher/Admin | `get_topic_performance_analytics` | `topic_scores` |
| `/analytics/weak-topics` | `GET` | Access Token | Student | `get_weak_topics` | `topic_scores` |
| `/analytics/jobs/failed` | `GET` | Access Token | Super Admin | `list_failed_analytics_jobs` | `dead_letter_events` |
| `/analytics/jobs/failed/{dead_letter_id}/retry` | `POST` | Access Token | Super Admin | `retry_failed_analytics_job` | `dead_letter_events` |
| `/ops/audit/feature-flags` | `GET` | Access Token | Admin | `list_feature_flag_audit_logs` | `audit_logs` |
| `/ops/audit/feature-flags/export` | `GET` | Access Token | Admin | `export_feature_flag_audit_logs` | `audit_logs` |
| `/ops/audit/feature-flags/names` | `GET` | Access Token | Admin | `list_feature_flag_audit_names` | `audit_logs` |
| `/ops/feature-flags` | `GET` | Access Token | Public | `list_feature_flags` | `feature_flags` |
| `/ops/feature-flags/catalog` | `GET` | Access Token | Admin | `feature_flag_catalog` | `feature_flags` |
| `/ops/feature-flags/{flag_name}` | `POST` | Access Token | Admin | `update_feature_flag` | `feature_flags` |
| `/ops/outbox` | `GET` | Access Token | Admin | `list_outbox_events` | `outbox_events` |
| `/ops/outbox/flush` | `POST` | Access Token | Admin | `flush_outbox_events` | `outbox_events` |
| `/ops/outbox/recover-stuck` | `POST` | Access Token | Admin | `recover_stuck_outbox_events` | `outbox_events` |
| `/ops/outbox/requeue-dead` | `POST` | Access Token | Admin | `requeue_dead_outbox_events` | `outbox_events` |
| `/ops/outbox/requeue-dead/{event_id}` | `POST` | Access Token | Admin | `requeue_one_dead_outbox_event` | `outbox_events` |
| `/ops/outbox/stats` | `GET` | Access Token | Admin | `outbox_stats` | `outbox_events` |

### Primary Endpoint Detail: `POST /analytics/precomputed/refresh`
*   **Validation**: Admin role check.
*   **Services Called**: [PrecomputedAnalyticsService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/precomputed_analytics_service.py)
*   **Repositories**: [UserRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
*   **Exceptions**: `HTTP 403 Forbidden` (Unauthorized role access).
*   **Performance Notes**: Offloads tasks asynchronously to Celery workers to protect db pools from blocking.
*   **Related Frontend Pages**: `/admin` in [app/(admin)/admin/page.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/app/(admin)/admin/page.tsx)
*   **Related Tests**: [backend/tests/integration/test_analytics.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_analytics.py)
*   **Swagger Example**:
    ```json
    {
      "request": {},
      "response": { "task_queued": true, "task_id": "recalc-job-99" }
    }
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        Client->>API: POST /analytics/precomputed/refresh
        API->>PrecomputedAnalyticsService: trigger_recalc()
        PrecomputedAnalyticsService->>Celery: Publish Task
        API-->>Client: Task confirmation JSON
    ```

---

## Group 7: Community & Social Router (17 Endpoints)

| Endpoint | Method | Authentication | Permissions | Endpoint Function | Database Tables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/community/communities` | `GET` | Access Token | Student | `list_communities` | `communities` |
| `/community/communities` | `POST` | Access Token | Admin | `create_community` | `communities` |
| `/community/communities/{community_id}` | `DELETE` | Access Token | Admin | `delete_community` | `communities` |
| `/community/members` | `GET` | Access Token | Student | `list_members` | `community_members` |
| `/community/members` | `POST` | Access Token | Student | `join_community` | `community_members` |
| `/community/threads` | `GET` | Access Token | Student | `list_threads` | `discussion_threads` |
| `/community/threads` | `POST` | Access Token | Student | `create_thread` | `discussion_threads` |
| `/community/threads/{thread_id}/resolve` | `PATCH` | Access Token | Student/Admin | `resolve_thread` | `discussion_threads` |
| `/community/replies` | `GET` | Access Token | Student | `list_replies` | `discussion_replies` |
| `/community/replies` | `POST` | Access Token | Student | `create_reply` | `discussion_replies` |
| `/community/badges` | `GET` | Access Token | Student | `list_badges` | `badges` |
| `/community/badges` | `POST` | Access Token | Admin | `award_badge` | `badges`, `user_badges` |
| `/community/badges/{badge_id}` | `DELETE` | Access Token | Admin | `revoke_badge` | `user_badges` |
| `/social/follows` | `POST` | Access Token | Student | `follow_user` | `social_follows` |
| `/social/follows/{followed_user_id}` | `DELETE` | Access Token | Student | `unfollow_user` | `social_follows` |
| `/social/network` | `GET` | Access Token | Student | `get_social_network` | `social_follows` |
| `/notifications` | `GET` | Access Token | Student | `list_notifications` | `notifications` |
| `/notifications/generate` | `POST` | Access Token | Admin | `generate_notifications` | `notifications` |
| `/notifications/{notification_id}/read` | `POST` | Access Token | Student | `mark_notification_read` | `notifications` |

### Primary Endpoint Detail: `POST /community/threads`
*   **Validation**: Enforces non-empty thread titles.
*   **Services Called**: [CommunityService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/community_service.py)
*   **Repositories**: [UserRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
*   **Exceptions**: `HTTP 400 Bad Request` (Invalid payload parameter values).
*   **Performance Notes**: Database transactions lock parent community entities to sync thread count indexes.
*   **Related Frontend Pages**: `/community` in [app/community/page.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/app/community/page.tsx)
*   **Related Tests**: [backend/tests/integration/test_community.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_community.py)
*   **Swagger Example**:
    ```json
    {
      "request": { "community_id": 3, "title": "Graph Traversal Help", "content": "I am stuck on Topological Sort..." },
      "response": { "thread_id": 142, "title": "Graph Traversal Help", "created_at": "timestamp" }
    }
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        Client->>API: POST /community/threads
        API->>CommunityService: create_thread()
        CommunityService->>DB: INSERT INTO discussion_threads
        CommunityService-->>API: Created Thread payload
        API-->>Client: Thread JSON
    ```

---

## Group 8: Ecosystem & Billing Router (10 Endpoints)

| Endpoint | Method | Authentication | Permissions | Endpoint Function | Database Tables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/ecosystem/overview` | `GET` | Access Token | Student | `ecosystem_overview` | `tenants` |
| `/ecosystem/api-clients` | `GET` | Access Token | Admin | `list_api_clients` | `api_clients` |
| `/ecosystem/api-clients` | `POST` | Access Token | Admin | `create_api_client` | `api_clients` |
| `/ecosystem/marketplace` | `GET` | Access Token | Student | `list_marketplace` | `marketplace_listings` |
| `/ecosystem/marketplace` | `POST` | Access Token | Admin | `create_marketplace_listing` | `marketplace_listings` |
| `/ecosystem/marketplace/{listing_id}/reviews` | `POST` | Access Token | Student | `create_marketplace_review` | `marketplace_reviews` |
| `/ecosystem/plugins` | `GET` | Access Token | Admin | `list_plugins` | `plugin_registry` |
| `/ecosystem/plugins` | `POST` | Access Token | Admin | `create_plugin` | `plugin_registry` |
| `/ecosystem/subscription` | `POST` | Access Token | Admin | `assign_subscription` | `tenant_subscriptions` |
| `/ecosystem/subscription-plans` | `GET` | Access Token | Student | `list_subscription_plans` | `subscription_plans` |
| `/ecosystem/subscription-plans` | `POST` | Access Token | Admin | `create_subscription_plan` | `subscription_plans` |

### Primary Endpoint Detail: `POST /ecosystem/api-clients`
*   **Validation**: Validates request domain schemas.
*   **Services Called**: [EcosystemService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/ecosystem_service.py)
*   **Repositories**: [UserRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
*   **Exceptions**: `HTTP 409 Conflict` (Domain name already registered).
*   **Performance Notes**: Scopes API access client scopes using dynamic RLS parameters.
*   **Related Frontend Pages**: `/admin/settings`
*   **Related Tests**: [backend/tests/integration/test_ecosystem.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_ecosystem.py)
*   **Swagger Example**:
    ```json
    {
      "request": { "client_name": "PartnerApp", "domain_origin": "https://partner.com" },
      "response": { "client_id": "cid-98", "api_key_secret": "secret_key" }
    }
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        Client->>API: POST /ecosystem/api-clients
        API->>EcosystemService: create_api_client()
        EcosystemService->>DB: INSERT INTO api_clients
        EcosystemService-->>API: Created Client credentials
        API-->>Client: Client credentials JSON
    ```

---

## Group 9: Profile & User Router (12 Endpoints)

| Endpoint | Method | Authentication | Permissions | Endpoint Function | Database Tables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/profile` | `GET` | Access Token | Student | `get_profile` | `users` |
| `/profile` | `POST` | Access Token | Student | `create_or_update_profile` | `users` |
| `/profile/status` | `GET` | Access Token | Student | `profile_status` | `users` |
| `/profile/progress` | `GET` | Access Token | Student | `profile_progress` | `roadmap_steps`, `topic_scores` |
| `/profile/onboarding-events` | `POST` | Access Token | Student | `track_onboarding_event` | `learning_events` |
| `/profile/upload-photo` | `POST` | Access Token | Student | `upload_profile_photo` | `file_assets` |
| `/users` | `POST` | Access Token | Admin | `create_user` | `users` |
| `/users/create` | `POST` | Access Token | Admin | `create_user_alias` | `users` |
| `/users` | `GET` | Access Token | Admin | `list_users` | `users` |
| `/users/list` | `GET` | Access Token | Admin | `list_users_alias` | `users` |
| `/users/me` | `GET` | Access Token | Student | `get_me` | `users` |
| `/users/me` | `PATCH` | Access Token | Student | `update_me` | `users` |
| `/users/complete-profile` | `PUT` | Access Token | Student | `complete_profile` | `users` |

### Primary Endpoint Detail: `PUT /users/complete-profile`
*   **Validation**: Confirms that request profiles contain required contact details.
*   **Services Called**: [UserService](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/user_service.py)
*   **Repositories**: [UserRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
*   **Exceptions**: `HTTP 400 Bad Request` (Missing required profile parameters).
*   **Performance Notes**: Clears user session cache structures in Redis on update execution.
*   **Related Frontend Pages**: `/onboarding`
*   **Related Tests**: [backend/tests/integration/test_user.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_user.py)
*   **Swagger Example**:
    ```json
    {
      "request": { "full_name": "Jane Doe", "college_name": "State University" },
      "response": { "email": "user@tenant.com", "is_profile_completed": true }
    }
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        Client->>API: PUT /users/complete-profile
        API->>UserService: complete_profile()
        UserService->>DB: UPDATE users SET is_profile_completed=true
        UserService->>Redis: Delete User Cache
        UserService-->>API: Updated User profile
        API-->>Client: User profile JSON
    ```

---

## Group 10: Realtime & Core Services Router (8 Endpoints)

| Endpoint | Method | Authentication | Permissions | Endpoint Function | Database Tables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/realtime/ws` | None | Access Token (URL Query) | Student | `realtime_websocket` | None |
| `/health` | `GET` | None | Public | `health` | Checks PG, Redis, Celery connection status |
| `/metrics` | `GET` | None | Public (Internal-only) | `metrics` | None |
| `/files/upload-request` | `POST` | Access Token | Student | `create_upload_request` | `file_assets` |
| `/files/finalize` | `POST` | Access Token | Student | `finalize_upload` | `file_assets` |
| `/files/{asset_id}` | `GET` | Access Token | Student | `get_file_download` | `file_assets` |
| `/career/interview-prep` | `POST` | Access Token | Student | `interview_prep` | `mentor_chat_messages` |
| `/career/overview` | `GET` | Access Token | Student | `career_overview` | `job_roles` |
| `/career/readiness` | `GET` | Access Token | Student | `career_readiness` | `job_role_skills` |
| `/career/resume` | `GET` | Access Token | Student | `career_resume` | `file_assets` |
| `/career/roles/bootstrap` | `POST` | Access Token | Admin | `bootstrap_career_roles` | `job_roles` |

### Primary Endpoint Detail: `GET /health`
*   **Validation**: None.
*   **Services Called**: Direct DB Session validation, Redis connection ping checks.
*   **Exceptions**: Returns health checks containing detailed failure logs if connection endpoints timeout.
*   **Performance Notes**: Queries Postgres `SELECT 1` and pings Redis to verify service states.
*   **Related Frontend Pages**: None.
*   **Related Tests**: [backend/tests/integration/test_health.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_health.py)
*   **Swagger Example**:
    ```json
    {
      "request": {},
      "response": { "database": {"status": "ok"}, "redis": {"status": "ok"}, "celery": {"status": "ok"} }
    }
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        Client->>API: GET /health
        API->>DB: SELECT 1
        API->>Redis: PING
        API->>Celery: Inspectcontrol
        API-->>Client: Health status payload JSON
    ```
