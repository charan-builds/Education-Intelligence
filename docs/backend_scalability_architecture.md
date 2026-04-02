# Backend Scalability Architecture

## Domain Separation

Application service domains are now grouped under `backend/app/application/domains/` without breaking existing imports:

- `learning`
  - diagnostic
  - roadmap
  - goals
  - topics
  - learning events
- `analytics`
  - analytics
  - retention
  - skill vectors
  - precomputed analytics
- `ml`
  - feature store
  - learning intelligence
  - ML platform
- `community`
  - community
  - mentor
  - social network

Recommended next step:
- move route registration to domain routers
- move repositories into matching domain packages
- enforce import direction: `presentation -> application/domains -> infrastructure`

## Event-Driven Architecture

Current outbox-backed events:

- `learning_event.recorded`
- `notification.created`
- `analytics.snapshot_refreshed`

Explicit domain events now emitted through the outbox:

- `diagnostic_completed`
- `roadmap_generated`
- `user_progress_updated`

Recommended consumers:

- analytics projector
- notification generator
- ML feature snapshot refresher
- mentor recommendation refresher

## AI / ML Service Split

Current state:

- backend still owns feature snapshots, model registry, and training metadata
- `ai_service` owns LLM-heavy operations:
  - roadmap generation
  - mentor response
  - progress analysis
  - topic explanation
  - question generation

Safe migration path:

1. Keep current backend `/ml/*` endpoints as compatibility routes.
2. Move inference-only HTTP handlers first behind `ai_service`.
3. Emit async outbox tasks for heavier AI/ML jobs:
   - `jobs.ai_generate_roadmap`
   - `jobs.ai_analyze_progress`
   - `jobs.ai_generate_questions`
4. Keep model registry and training metadata in backend until externalized.

## Database Hardening

High-value indexes to add first:

- `learning_events (tenant_id, user_id, event_timestamp desc)`
- `diagnostic_tests (user_id, completed_at desc)`
- `roadmaps (user_id, status, id desc)`
- `roadmap_steps (roadmap_id, progress_status, priority)`
- `questions (topic_id, difficulty, id)`
- `community_members (tenant_id, community_id, user_id)`
- `discussion_threads (tenant_id, community_id, created_at desc)`
- `discussion_replies (tenant_id, thread_id, created_at asc)`
- `topic_scores (tenant_id, user_id, topic_id)`
- `user_skill_vectors (tenant_id, user_id, topic_id)`
- `outbox_events (status, available_at, id)`

See `docs/postgres_index_recommendations.sql`.

## PostgreSQL RLS Preparation

Recommended rollout:

1. add session tenant context via `set_config('app.current_tenant_id', ...)`
2. enable RLS on direct tenant tables
3. add join-based RLS for indirect tables
4. remove manual tenant filters gradually after verification

Tables to prioritize:

- users
- topics
- goals
- communities
- discussion_threads
- community_members
- notifications
- refresh_tokens
- learning_events
- topic_scores

## Performance Notes

Current heavy endpoints to keep cached:

- analytics overview
- topic mastery
- roadmap progress
- topic graph
- topic list
- AI service requests

Recommended next optimizations:

- add cache namespace invalidation by domain instead of broad analytics busts
- move expensive materialization refreshes fully behind background jobs
- paginate community moderation lists at larger scales with cursor pagination
- precompute learner heatmaps for `analytics/student/{user_id}`
