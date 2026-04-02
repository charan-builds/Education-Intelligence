-- Run with CREATE INDEX CONCURRENTLY in production maintenance windows.

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_learning_events_tenant_user_event_ts
ON learning_events (tenant_id, user_id, event_timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_diagnostic_tests_user_completed
ON diagnostic_tests (user_id, completed_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_roadmaps_user_status_id
ON roadmaps (user_id, status, id DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_roadmap_steps_roadmap_status_priority
ON roadmap_steps (roadmap_id, progress_status, priority);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_questions_topic_difficulty_id
ON questions (topic_id, difficulty, id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_community_members_tenant_community_user
ON community_members (tenant_id, community_id, user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_discussion_threads_tenant_community_created
ON discussion_threads (tenant_id, community_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_discussion_replies_tenant_thread_created
ON discussion_replies (tenant_id, thread_id, created_at ASC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_topic_scores_tenant_user_topic
ON topic_scores (tenant_id, user_id, topic_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_user_skill_vectors_tenant_user_topic
ON user_skill_vectors (tenant_id, user_id, topic_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_outbox_events_status_available_id
ON outbox_events (status, available_at, id);
