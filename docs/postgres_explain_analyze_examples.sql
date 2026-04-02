-- 1. Latest open diagnostic for a learner
EXPLAIN ANALYZE
SELECT id, user_id, goal_id, started_at, completed_at
FROM diagnostic_tests
WHERE user_id = 42
  AND goal_id = 7
  AND completed_at IS NULL
ORDER BY id DESC
LIMIT 1;

-- 2. Topic score aggregation for a completed diagnostic
EXPLAIN ANALYZE
SELECT q.topic_id, AVG(ua.score) AS avg_score
FROM user_answers ua
JOIN questions q ON q.id = ua.question_id
JOIN diagnostic_tests dt ON dt.id = ua.test_id
WHERE ua.test_id = 1001
  AND dt.user_id = 42
GROUP BY q.topic_id;

-- 3. Latest roadmap with steps for a learner
EXPLAIN ANALYZE
SELECT r.id, r.status, rs.id AS step_id, rs.topic_id, rs.priority, rs.progress_status
FROM roadmaps r
LEFT JOIN roadmap_steps rs ON rs.roadmap_id = r.id
WHERE r.user_id = 42
ORDER BY r.id DESC, rs.priority ASC
LIMIT 200;

-- 4. Community thread timeline
EXPLAIN ANALYZE
SELECT id, community_id, title, created_at
FROM discussion_threads
WHERE tenant_id = 1
  AND community_id = 12
ORDER BY created_at DESC, id DESC
LIMIT 50;

-- 5. Latest user learning summary snapshot
EXPLAIN ANALYZE
SELECT id, tenant_id, snapshot_type, subject_id, updated_at
FROM analytics_snapshots
WHERE tenant_id = 1
  AND snapshot_type = 'user_learning_summary'
  AND subject_id = 42
ORDER BY updated_at DESC
LIMIT 1;

-- 6. Outbox dispatcher polling
EXPLAIN ANALYZE
SELECT id, status, available_at
FROM outbox_events
WHERE status = 'pending'
  AND available_at <= now()
ORDER BY id ASC
LIMIT 100;
