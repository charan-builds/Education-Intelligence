-- Run with CREATE INDEX CONCURRENTLY in production maintenance windows.

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_users_tenant_created_at
ON users (tenant_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_learning_events_tenant_user_event_ts
ON learning_events (tenant_id, user_id, event_timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_diagnostic_tests_user_completed
ON diagnostic_tests (user_id, completed_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_diagnostic_tests_user_goal_open
ON diagnostic_tests (user_id, goal_id, completed_at, id DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_user_answers_test_question
ON user_answers (test_id, question_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_roadmaps_user_status_id
ON roadmaps (user_id, status, id DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_roadmap_steps_roadmap_status_priority
ON roadmap_steps (roadmap_id, progress_status, priority);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_roadmap_steps_roadmap_topic
ON roadmap_steps (roadmap_id, topic_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_questions_topic_difficulty_id
ON questions (topic_id, difficulty, id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_goal_topics_goal_topic
ON goal_topics (goal_id, topic_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_topic_prerequisites_topic_prereq
ON topic_prerequisites (topic_id, prerequisite_topic_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_community_members_tenant_community_user
ON community_members (tenant_id, community_id, user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_discussion_threads_tenant_community_created
ON discussion_threads (tenant_id, community_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_discussion_replies_tenant_thread_created
ON discussion_replies (tenant_id, thread_id, created_at ASC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_topic_scores_tenant_user_topic
ON topic_scores (tenant_id, user_id, topic_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_topic_scores_tenant_user_updated
ON topic_scores (tenant_id, user_id, updated_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_user_skill_vectors_tenant_user_topic
ON user_skill_vectors (tenant_id, user_id, topic_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_user_skill_vectors_tenant_user_updated
ON user_skill_vectors (tenant_id, user_id, last_updated DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_analytics_snapshots_tenant_type_subject_updated
ON analytics_snapshots (tenant_id, snapshot_type, subject_id, updated_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_analytics_snapshots_tenant_snapshot_latest
ON analytics_snapshots (tenant_id, snapshot_type, is_latest);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_analytics_snapshots_created_at_desc
ON analytics_snapshots (created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_outbox_events_status_available_id
ON outbox_events (status, available_at, id);
