Tenant RLS Audit - 2026-04-02

Summary

- Current tenant isolation is mixed-mode.
- PostgreSQL RLS exists, but only for a subset of tenant-scoped tables.
- Many repositories and some services still rely on manual `tenant_id` filters or `tenant_user_scope(...)`.
- That means the system is currently safe mostly by convention plus review discipline, not by uniform database enforcement.

Current RLS Coverage

The current script in [backend/sql/postgres_tenant_rls.sql](/home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls.sql) protects:

- `users`
- `topics`
- `goals`
- `roadmaps`
- `communities`
- `community_members`
- `discussion_threads`
- `discussion_replies`
- `analytics_snapshots`
- `learning_events`
- `notifications`
- `topic_scores`
- `questions`
- `roadmap_steps`
- `diagnostic_tests`

Tenant-Scoped Tables Missing RLS

Direct `tenant_id` tables missing RLS:

- `ai_requests`
- `api_clients`
- `audit_logs`
- `auth_logs`
- `auth_tokens`
- `authorization_policies`
- `badges`
- `content_metadata`
- `dead_letter_events`
- `diagnostic_test_states`
- `event_consumer_states`
- `experiments`
- `feature_flags`
- `file_assets`
- `gamification_events`
- `gamification_profiles`
- `job_roles`
- `marketplace_listings`
- `marketplace_reviews`
- `mentor_chat_messages`
- `mentor_memory_profiles`
- `mentor_messages`
- `mentor_session_memories`
- `mentor_students`
- `mentor_suggestions`
- `ml_feature_snapshots`
- `ml_model_registry`
- `ml_training_runs`
- `outbox_events`
- `plugin_registry`
- `processed_stream_events`
- `refresh_tokens`
- `resources`
- `sessions`
- `skills`
- `social_follows`
- `subscription_plans`
- `tenant_subscriptions`
- `token_blacklist`
- `topic_features`
- `user_features`
- `user_skill_vectors`
- `user_tenant_roles`

Derived-tenant tables missing RLS:

- `user_answers` via `diagnostic_tests -> users`
- `goal_topics` via `goals` and `topics`
- `topic_prerequisites` via `topics`
- `topic_skills` via `topics` and `skills`
- `job_role_skills` via `job_roles` and `skills`
- `refresh_sessions` via `users`
- `experiment_variants` via `experiments`

Operational tables that should be reviewed before enabling tenant RLS:

- `stream_consumer_offsets`
- `processed_stream_events`
- `event_consumer_states`
- `outbox_events`
- `dead_letter_events`

These are tenant-aware, but they are also used by shared worker infrastructure. They should get RLS only after confirming each worker path uses `open_tenant_session(...)` for tenant-scoped work and `open_system_session()` only for cross-tenant operational work.

Manual-Filter-Only Hotspots

These files show the current mixed enforcement most clearly:

- [backend/app/infrastructure/repositories/topic_repository.py](/home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/topic_repository.py)
- [backend/app/infrastructure/repositories/community_repository.py](/home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/community_repository.py)
- [backend/app/infrastructure/repositories/roadmap_repository.py](/home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/roadmap_repository.py)
- [backend/app/infrastructure/repositories/tenant_scoping.py](/home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/tenant_scoping.py)
- [backend/app/application/services/search_service.py](/home/charan_derangula/projects/intelligentSystems/backend/app/application/services/search_service.py)
- [backend/app/application/services/digital_twin_service.py](/home/charan_derangula/projects/intelligentSystems/backend/app/application/services/digital_twin_service.py)
- [backend/app/application/services/skill_vector_service.py](/home/charan_derangula/projects/intelligentSystems/backend/app/application/services/skill_vector_service.py)
- [backend/app/application/services/mentor_memory_service.py](/home/charan_derangula/projects/intelligentSystems/backend/app/application/services/mentor_memory_service.py)
- [backend/app/application/services/ai_context_builder.py](/home/charan_derangula/projects/intelligentSystems/backend/app/application/services/ai_context_builder.py)

Important Background-Job Note

[backend/app/infrastructure/database.py](/home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/database.py) is much better than before because tenant-scoped work now has to use `open_tenant_session(...)`. But `open_system_session()` sets `role="super_admin"`, which bypasses RLS for every table. That is correct for truly global maintenance work, but dangerous if used casually in tenant business flows.

Phase 1 Rollout

Safe immediate rollout:

1. Keep all manual repository filters in place.
2. Add RLS for the missing direct `tenant_id` tables first.
3. Add RLS for the clearly derived tables next:
   - `user_answers`
   - `refresh_sessions`
   - `goal_topics`
   - `topic_prerequisites`
   - `topic_skills`
   - `job_role_skills`
   - `experiment_variants`
4. Add integration tests that verify rows from another tenant are invisible even when a repository forgets the manual filter.

Phase 2 Rollout

After direct and derived business tables are covered:

1. Audit every `open_system_session()` call.
2. Restrict `open_system_session()` to:
   - health checks
   - schema/ops tasks
   - explicitly global scheduled maintenance
3. Convert tenant business jobs to `open_tenant_session(...)` only.
4. Then add RLS for tenant-aware operational tables like `outbox_events`, `dead_letter_events`, `event_consumer_states`, and `processed_stream_events`.

Phase 3 Rollout

Only after RLS coverage is proven in tests:

1. Keep repository `tenant_id` filters as defense in depth for a while.
2. Remove duplicated manual filters gradually from low-risk repositories first.
3. Do not remove join-based tenant assertions in one pass.

Performance Notes

- Keep tenant-leading indexes for every RLS-protected direct table.
- For derived tables, keep indexes on the foreign keys used by the RLS subquery:
  - `user_answers.test_id`
  - `refresh_sessions.user_id`
  - `goal_topics.goal_id`
  - `topic_prerequisites.topic_id`
  - `topic_prerequisites.prerequisite_topic_id`
  - `topic_skills.topic_id`
  - `topic_skills.skill_id`
  - `job_role_skills.job_role_id`
  - `job_role_skills.skill_id`
  - `experiment_variants.experiment_id`

Recommendation

Treat [backend/sql/postgres_tenant_rls.sql](/home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls.sql) as phase 1 and apply [backend/sql/postgres_tenant_rls_phase2.sql](/home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls_phase2.sql) next. Do not remove repository filters until the new SQL has been applied and verified in integration tests.
