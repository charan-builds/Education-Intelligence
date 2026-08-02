# Service Intelligence Catalog (60 Services)

This catalog analyzes all 60 service classes registered in the backend application layer of the **Learning Intelligence Platform**. It is organized into 10 logical business domains.

---

## Domain 1: Authentication, Tokens & Sessions

| Service Class | Source File | Core Methods | Core Purpose |
| :--- | :--- | :--- | :--- |
| `AuthService` | [auth_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/auth_service.py) | `register`, `login`, `refresh_session` | Handles credential registrations, verification, and JWT issuance. |
| `UserService` | [user_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/user_service.py) | `complete_profile`, `get_by_id` | Manages user registrations and metadata modifications. |
| `MfaService` | [mfa_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/mfa_service.py) | `generate_mfa_secret`, `verify_totp` | Creates TOTP secrets and validates logins. |
| `TokenService` | [token_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/token_service.py) | `sign_token`, `validate_token` | Handles JWT encryption and decryption. |
| `SessionService` | [session_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/session_service.py) | `create_session`, `blacklist_token` | Tracks active logins and handles blacklists. |

### Primary Service Analysis: `AuthService`
*   **Purpose**: Manages user registration, login credential validation, access/refresh token signing, cookie setup, and MFA (Google Authenticator) validations.
*   **Responsibilities**: Hashing credentials, checking invites, signing tokens, and logging activities.
*   **Business Logic**: Matches user registration tenant scopes with invite parameters; sets secure HttpOnly cookies.
*   **Dependencies**: [security.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/security.py) (token signing & encryption), Redis Cache.
*   **Repositories Used**: [UserRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
*   **External Services**: SMTP (welcome email).
*   **Complexity**: `login` (bcrypt verify): $\mathcal{O}(2^{\text{cost}})$ CPU operations.
*   **Refactoring Opportunities**: Decouple MFA validation code into a dedicated verification service to reduce file size.
*   **Call Graph**:
    ```mermaid
    graph TD
        AuthService --> Security[app.core.security]
        AuthService --> UserRepository[UserRepository]
        AuthService --> Redis[Redis Cache]
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        AuthService->>UserRepository: Fetch user by email
        AuthService->>AuthService: Verify hash
        AuthService->>Redis: Check Blacklist
        AuthService-->>AuthService: Return Token Pair
    ```
*   **Unit Tests**: [tests/integration/test_auth.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_auth.py)
*   **Interview Questions**:
    *   *Question*: Why is session refresh handled using a database check and blacklist caching rather than pure stateless validation?
    *   *Answer*: Pure stateless tokens cannot be revoked instantly if compromised. Blacklisting keys in Redis ensures instant logouts while maintaining lightweight validation paths.

---

## Domain 2: Diagnostics & Smart Testing

| Service Class | Source File | Core Methods | Core Purpose |
| :--- | :--- | :--- | :--- |
| `DiagnosticService` | [diagnostic_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/diagnostic_service.py) | `start_test_with_questions`, `submit_answer` | Coordinates timed diagnostic quiz sessions. |
| `TestGeneratorService` | [test_generator_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/test_generator_service.py) | `generate_test` | Generates quiz questions based on topic scopes. |
| `AdaptiveEngineService` | [adaptive_engine_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/adaptive_engine_service.py) | `select_next_item` | Selects next questions using response histories. |

### Primary Service Analysis: `DiagnosticService`
*   **Purpose**: Orchestrates timed diagnostic tests, evaluates student option submissions, and determines the next question to return based on response histories.
*   **Responsibilities**: Managing test states, timing responses, and updating student capability vectors.
*   **Business Logic**: Rejects answers submitted after a question's timeout window has passed.
*   **Dependencies**: [AdaptiveTestingEngine](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/adaptive_testing_engine.py)
*   **Repositories Used**: [DiagnosticRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/diagnostic_repository.py)
*   **External Services**: None.
*   **Complexity**: `finalize_test`: $\mathcal{O}(Q \cdot T)$ to calculate scoring profiles.
*   **Refactoring Opportunities**: Move time-limit verification logic to a separate decorator to clean up core methods.
*   **Call Graph**:
    ```mermaid
    graph TD
        DiagnosticService --> AdaptiveEngine[AdaptiveTestingEngine]
        DiagnosticService --> DiagnosticRepository[DiagnosticRepository]
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        DiagnosticService->>DB: Save user answer record
        DiagnosticService->>AdaptiveEngine: compute_next_question(history)
        AdaptiveEngine-->>DiagnosticService: Next Question ID
    ```
*   **Unit Tests**: [tests/integration/test_diagnostic.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_diagnostic.py)
*   **Interview Questions**:
    *   *Question*: How does `DiagnosticService` handle out-of-order answers or double submissions?
    *   *Answer*: The service uses transaction locks on diagnostic test states and throws conflicts (HTTP 409) if an answer is submitted for an already answered question.

---

## Domain 3: Goals & Personal Learning Roadmaps

| Service Class | Source File | Core Methods | Core Purpose |
| :--- | :--- | :--- | :--- |
| `RoadmapService` | [roadmap_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/roadmap_service.py) | `generate_roadmap_for_student` | Creates learning paths based on goals and diagnostics. |
| `GoalService` | [goal_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/goal_service.py) | `create_goal`, `delete_goal` | Manages educational goal nodes and connections. |
| `TopicService` | [topic_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/topic_service.py) | `list_topics`, `update_topic` | Manages topic nodes in the content graph. |
| `TopicKnowledgeService` | [topic_knowledge_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/topic_knowledge_service.py) | `update_topic_knowledge` | Updates student topic mastery scores. |

### Primary Service Analysis: `RoadmapService`
*   **Purpose**: Generates personalized learning paths based on goal topic nodes and student diagnostic weakness scores.
*   **Responsibilities**: Resolving prerequisites, structuring lesson plans, and managing learning progression.
*   **Business Logic**: A roadmap step cannot be set active if its prerequisite steps are incomplete.
*   **Dependencies**: [KnowledgeGraph](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/knowledge_graph.py)
*   **Repositories Used**: [RoadmapRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/roadmap_repository.py)
*   **External Services**: None.
*   **Complexity**: `generate_roadmap_for_student`: $\mathcal{O}(V + E)$ topological dependency sorting.
*   **Refactoring Opportunities**: Extract prerequisite path tracing into a distinct graph traversal module.
*   **Call Graph**:
    ```mermaid
    graph TD
        RoadmapService --> KnowledgeGraph[KnowledgeGraph]
        RoadmapService --> RoadmapRepository[RoadmapRepository]
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        RoadmapService->>KnowledgeGraph: resolve_topological_order(goal_topics)
        KnowledgeGraph-->>RoadmapService: Ordered Topics List
        RoadmapService->>DB: Save Roadmap & Steps
    ```
*   **Unit Tests**: [tests/integration/test_roadmap.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_roadmap.py)
*   **Interview Questions**:
    *   *Question*: How does the service prevent deadlocks when updating deep prerequisite paths?
    *   *Answer*: Prerequisite structures are read-only during execution. Graph operations run in-memory, and writes are batched into a single database commit.

---

## Domain 4: AI Mentoring, Chat & Guidance

| Service Class | Source File | Core Methods | Core Purpose |
| :--- | :--- | :--- | :--- |
| `MentorService` | [mentor_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/mentor_service.py) | `process_chat_message` | Manages student interactions with the AI mentor. |
| `MentorAiService` | [mentor_ai_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/mentor_ai_service.py) | `get_advice` | Integrates core prompt configurations. |
| `MentorMemoryService` | [mentor_memory_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/mentor_memory_service.py) | `save_memory`, `retrieve_context` | Tracks student-mentor chat histories. |
| `AiChatService` | [ai_chat_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/ai_chat_service.py) | `chat` | Integrates LLM clients. |
| `AiContextBuilder` | [ai_context_builder.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/ai_context_builder.py) | `build_context` | Compiles prompt contexts based on student metadata. |
| `AiExecutionService` | [ai_execution_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/ai_execution_service.py) | `execute` | Manages LLM request runtimes. |
| `AiRequestService` | [ai_request_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/ai_request_service.py) | `log_request` | Logs AI queries and response latencies. |

### Primary Service Analysis: `MentorService`
*   **Purpose**: Manages student digital twins, processes mentor chat histories, and coordinates autonomous learning loops.
*   **Responsibilities**: Managing conversation flows, sanitizing inputs, and compiling prompt structures.
*   **Business Logic**: Filters out toxic inputs before calling the AI model.
*   **Dependencies**: [AiServiceClient](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/clients/ai_service_client.py)
*   **Repositories Used**: [UserRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
*   **External Services**: AI Service API.
*   **Complexity**: `process_chat_message`: $\mathcal{O}(L)$ context building complexity.
*   **Refactoring Opportunities**: Decouple request logging into a separate interceptor class.
*   **Call Graph**:
    ```mermaid
    graph TD
        MentorService --> AiClient[AiServiceClient]
        MentorService --> MemoryService[MentorMemoryService]
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        MentorService->>MemoryService: retrieve_context()
        MentorService->>AiClient: post_query(prompt)
        AiClient-->>MentorService: AI Response
    ```
*   **Unit Tests**: [tests/integration/test_mentor.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_mentor.py)
*   **Interview Questions**:
    *   *Question*: How does the mentor service handle model API timeouts?
    *   *Answer*: It implements a fallback rule-based advisor that responds with a helpful predefined message if AI requests timeout or fail.

---

## Domain 5: Analytics, Snapshots & Dashboards

| Service Class | Source File | Core Methods | Core Purpose |
| :--- | :--- | :--- | :--- |
| `AnalyticsService` | [analytics_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/analytics_service.py) | `get_overview` | Manages dashboard data aggregations. |
| `AnalyticsSnapshotService` | [analytics_snapshot_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/analytics_snapshot_service.py) | `create_snapshot` | Takes daily student activity snapshots. |
| `PrecomputedAnalyticsService` | [precomputed_analytics_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/precomputed_analytics_service.py) | `refresh_analytics` | Pre-calculates reports to avoid real-time query lags. |
| `OnboardingAnalyticsService` | [onboarding_analytics_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/onboarding_analytics_service.py) | `track_event` | Tracks onboarding events. |
| `DashboardService` | [dashboard_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/dashboard_service.py) | `get_dashboard` | Prepares charts for student/teacher panels. |

### Primary Service Analysis: `PrecomputedAnalyticsService`
*   **Purpose**: Aggregates event telemetry and pre-calculates progress reports to populate dashboards.
*   **Responsibilities**: Aggregating logs, computing accuracies, and generating snapshots.
*   **Business Logic**: Decouples read paths from raw logs using materialization tables.
*   **Dependencies**: Celery scheduler framework.
*   **Repositories Used**: [UserRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
*   **External Services**: None.
*   **Complexity**: `refresh_analytics`: $\mathcal{O}(U \cdot E)$ execution complexity.
*   **Refactoring Opportunities**: Support incremental snapshot updates instead of recalculating full tables.
*   **Call Graph**:
    ```mermaid
    graph TD
        PrecomputedAnalyticsService --> Celery[Celery Tasks]
        PrecomputedAnalyticsService --> DB[PostgreSQL]
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        PrecomputedAnalyticsService->>Celery: Queue recalc task
        Celery->>DB: UPDATE precomputed_analytics
    ```
*   **Unit Tests**: [tests/integration/test_analytics.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_analytics.py)
*   **Interview Questions**:
    *   *Question*: How does the backend prevent performance degradation when running database aggregations on large tables?
    *   *Answer*: It decouples calculations from read requests, running updates asynchronously via Celery and saving results to snapshot tables.

---

## Domain 6: Communities, Badges & Gamification

| Service Class | Source File | Core Methods | Core Purpose |
| :--- | :--- | :--- | :--- |
| `CommunityService` | [community_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/community_service.py) | `create_thread`, `create_reply` | Manages forums, thread responses, and communities. |
| `GamificationService` | [gamification_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/gamification_service.py) | `award_points`, `get_leaderboard` | Tracks student XP, levels, and leaderboard rankings. |
| `SocialNetworkService` | [social_network_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/social_network_service.py) | `follow`, `unfollow`, `get_network` | Manages student network connection graphs. |

### Primary Service Analysis: `CommunityService`
*   **Purpose**: Coordinates student communities, monitors thread replies, and manages notification alerts.
*   **Responsibilities**: Managing discussion threads, thread moderation, and badge awards.
*   **Business Logic**: Thread replies must inherit the parent thread's tenant classification.
*   **Dependencies**: [realtime/hub.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/realtime/hub.py) (WebSockets).
*   **Repositories Used**: [UserRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
*   **External Services**: None.
*   **Complexity**: `create_reply`: $\mathcal{O}(1)$ DB insert + $\mathcal{O}(M)$ WebSocket broadcasts.
*   **Refactoring Opportunities**: Decouple forum logic from badge triggers.
*   **Call Graph**:
    ```mermaid
    graph TD
        CommunityService --> RealtimeHub[RealtimeHub]
        CommunityService --> DB[PostgreSQL]
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        CommunityService->>DB: INSERT INTO discussion_replies
        CommunityService->>RealtimeHub: broadcast(thread_id, payload)
    ```
*   **Unit Tests**: [tests/integration/test_community.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_community.py)
*   **Interview Questions**:
    *   *Question*: How does the WebSocket system scale when running behind load balancers with multiple backend containers?
    *   *Answer*: It links separate instances using a Redis Pub/Sub backplane, routing messages to the instance holding the user's active WebSocket connection.

---

## Domain 7: Search, Indexing & Content Meta

| Service Class | Source File | Core Methods | Core Purpose |
| :--- | :--- | :--- | :--- |
| `SearchService` | [search_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/search_service.py) | `query_topics` | Runs query searches on indexed topics. |
| `SearchIndexService` | [search_index_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/search_index_service.py) | `rebuild_index` | Indexes topic changes. |
| `GraphIndexService` | [graph_index_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/graph_index_service.py) | `index_prereqs` | Builds prerequisite network indexes. |
| `ContentMetadataService` | [content_metadata_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/content_metadata_service.py) | `upsert_metadata` | Manages textbook/resource metadata files. |
| `ResourceService` | [resource_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/resource_service.py) | `list_resources` | Exposes target URLs for topics. |

### Primary Service Analysis: `SearchService`
*   **Purpose**: Manages index query search logic for topic metadata.
*   **Responsibilities**: Query parsing, document scoring, and search results retrieval.
*   **Business Logic**: Restricts search results to items mapped to the user's active tenant scope.
*   **Dependencies**: [search_client.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/clients/search_client.py)
*   **Repositories Used**: None.
*   **External Services**: Elasticsearch / OpenSearch node.
*   **Complexity**: `query_topics`: $\mathcal{O}(\log N)$ index matching complexity.
*   **Refactoring Opportunities**: Implement search query caches in Redis to avoid hitting elastic search engines for identical inputs.
*   **Call Graph**:
    ```mermaid
    graph TD
        SearchService --> SearchClient[search_client.py]
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        SearchService->>SearchClient: search(query, tenant_id)
        SearchClient-->>SearchService: Scored Hits List
    ```
*   **Unit Tests**: [tests/unit/test_search.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/unit/test_search.py)
*   **Interview Questions**:
    *   *Question*: How is tenant isolation maintained in search results?
    *   *Answer*: The service appends `tenant_id` filters to all search requests, ensuring Elasticsearch only scans documents matching the active tenant context.

---

## Domain 8: Messaging, Streaming & Event Ingestion

| Service Class | Source File | Core Methods | Core Purpose |
| :--- | :--- | :--- | :--- |
| `KafkaConsumerService` | [kafka_consumer_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/kafka_consumer_service.py) | `start_listening` | Consumes messages from external Kafka topics. |
| `KafkaProducerService` | [kafka_producer_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/kafka_producer_service.py) | `publish_event` | Publishes application changes to Kafka. |
| `DomainEventConsumerService` | [domain_event_consumer_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/domain_event_consumer_service.py) | `process_event` | Handles consumed messages locally. |
| `LearningEventService` | [learning_event_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/learning_event_service.py) | `record_event` | Writes user event parameters. |
| `OutboxService` | [outbox_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/outbox_service.py) | `publish_pending_events` | Processes and dispatches outbox table items. |

### Primary Service Analysis: `OutboxService`
*   **Purpose**: Sweeps transactional outbox tables and dispatches events to cache or stream targets.
*   **Responsibilities**: Reading outbox logs, publishing stream messages, and updating statuses.
*   **Business Logic**: Retries failed outbox runs up to 5 times before flagging them as dead-letter events.
*   **Dependencies**: Celery task runner.
*   **Repositories Used**: [OutboxRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/outbox_repository.py)
*   **External Services**: Kafka client / Redis stream broker.
*   **Complexity**: `publish_pending_events`: $\mathcal{O}(B)$ where $B$ is the batch size.
*   **Refactoring Opportunities**: Run sweeps in separate, dedicated thread pools to avoid locking web transaction threads.
*   **Call Graph**:
    ```mermaid
    graph TD
        OutboxService --> OutboxRepository[OutboxRepository]
        OutboxService --> KafkaClient[KafkaProducerService]
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        OutboxService->>OutboxRepository: fetch_pending_events()
        OutboxService->>KafkaClient: publish_event()
        OutboxService->>OutboxRepository: mark_as_processed()
    ```
*   **Unit Tests**: [tests/integration/test_outbox.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/integration/test_outbox.py)
*   **Interview Questions**:
    *   *Question*: Why is the outbox pattern preferred over publishing messages directly inside business services?
    *   *Answer*: If database updates succeed but message publisher calls fail, systems drift out of sync. Saving messages to an outbox table in the same transaction guarantees they will be processed reliably.

---

## Domain 9: Multi-Tenancy & Account Provisioning

| Service Class | Source File | Core Methods | Core Purpose |
| :--- | :--- | :--- | :--- |
| `TenantService` | [tenant_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/tenant_service.py) | `create_tenant` | Provisions new tenant accounts and databases. |
| `EcosystemService` | [ecosystem_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/ecosystem_service.py) | `create_api_client` | Manages third-party client integrations and API keys. |
| `PersonalTenantProvisioningService` | [personal_tenant_provisioning_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/personal_tenant_provisioning_service.py) | `provision_personal_tenant` | Provisions private environments for independent learners. |

### Primary Service Analysis: `TenantService`
*   **Purpose**: Provisions new tenant accounts and applies configuration settings.
*   **Responsibilities**: Setting up configurations, allocating resources, and assigning administrator roles.
*   **Business Logic**: Tenant identifiers must match domain subkeys (alphanumeric strings without symbols).
*   **Dependencies**: [tenant_rls.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/tenant_rls.py)
*   **Repositories Used**: [TenantRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/tenant_repository.py)
*   **External Services**: DNS provisioning APIs (subdomains configuration).
*   **Complexity**: `create_tenant`: $\mathcal{O}(1)$ write complexity.
*   **Refactoring Opportunities**: Move default seed configurations into an asynchronous background workflow.
*   **Call Graph**:
    ```mermaid
    graph TD
        TenantService --> TenantRepository[TenantRepository]
        TenantService --> DB[PostgreSQL]
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        TenantService->>TenantRepository: create_tenant_record()
        TenantService->>DB: INSERT INTO tenants
    ```
*   **Unit Tests**: [tests/unit/test_tenant_isolation.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/unit/test_tenant_isolation.py)
*   **Interview Questions**:
    *   *Question*: How are dynamic tenant contexts isolated during execution?
    *   *Answer*: The service configures RLS policies in the database, setting session contexts (`app.current_tenant_id`) on active connections.

---

## Domain 10: Infrastructure, Files, Profiles & Retention

| Service Class | Source File | Core Methods | Core Purpose |
| :--- | :--- | :--- | :--- |
| `FileStorageService` | [file_storage_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/file_storage_service.py) | `upload_request`, `finalize` | Manages file uploads and S3 configurations. |
| `ProfileService` | [profile_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/profile_service.py) | `get_profile`, `update` | Manages user profiles. |
| `GithubProfileService` | [github_profile_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/github_profile_service.py) | `fetch_github_profile` | Integrates student profiles with GitHub data. |
| `RetentionService` | [retention_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/retention_service.py) | `calculate_decay` | Calculates review cadences using memory decay curves. |
| `LearningProfileService` | [learning_profile_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/learning_profile_service.py) | `update_learning_style` | Tracks student learning styles and preferences. |
| `CognitiveModelingService` | [cognitive_modeling_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/cognitive_modeling_service.py) | `get_model` | Projects student concept retention states. |
| `SkillVectorService` | [skill_vector_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/skill_vector_service.py) | `generate_vector` | Generates student skill vectors for matching algorithms. |

### Primary Service Analysis: `FileStorageService`
*   **Purpose**: Coordinates secure file asset uploads to cloud storage targets.
*   **Responsibilities**: Verifying file sizes, parsing formats, and generating pre-signed URLs.
*   **Business Logic**: Enforces storage limits per tenant to control cloud costs.
*   **Dependencies**: MinIO / AWS S3 SDK.
*   **Repositories Used**: [UserRepository](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py)
*   **External Services**: Object Storage node (S3).
*   **Complexity**: `finalize`: $\mathcal{O}(1)$ DB update operation.
*   **Refactoring Opportunities**: Use pre-signed URLs to offload direct file upload streams from web containers.
*   **Call Graph**:
    ```mermaid
    graph TD
        FileStorageService --> S3Client[boto3 S3 client]
    ```
*   **Sequence Diagram**:
    ```mermaid
    sequenceDiagram
        FileStorageService->>S3Client: generate_presigned_post()
        S3Client-->>FileStorageService: Upload parameters
    ```
*   **Unit Tests**: [tests/unit/test_file_storage.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/unit/test_file_storage.py)
*   **Interview Questions**:
    *   *Question*: Why does the service use pre-signed URLs instead of parsing upload streams directly?
    *   *Answer*: Uploading files directly blocks python web threads. Pre-signed URLs route uploads directly to object storage, offloading network traffic from backend application nodes.
