"""analytics materialized views

Revision ID: 20260328_0003
Revises: 20260327_0002
Create Date: 2026-03-28 00:00:03.000000
"""

from alembic import op


revision = "20260328_0003"
down_revision = "20260327_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE MATERIALIZED VIEW tenant_analytics_mv AS
        WITH latest_completed_tests AS (
            SELECT dt.user_id, MAX(dt.id) AS test_id
            FROM diagnostic_tests dt
            WHERE dt.completed_at IS NOT NULL
            GROUP BY dt.user_id
        ),
        topic_avg AS (
            SELECT
                utr.tenant_id,
                q.topic_id,
                AVG(ua.score) AS avg_score
            FROM latest_completed_tests lct
            JOIN diagnostic_tests dt ON dt.id = lct.test_id
            JOIN user_tenant_roles utr ON utr.user_id = dt.user_id AND utr.role = 'student'
            JOIN user_answers ua ON ua.test_id = dt.id
            JOIN questions q ON q.id = ua.question_id
            GROUP BY utr.tenant_id, q.topic_id
        ),
        topic_distribution AS (
            SELECT
                tenant_id,
                COUNT(*) FILTER (WHERE avg_score < 50) AS beginner_topics,
                COUNT(*) FILTER (WHERE avg_score >= 50 AND avg_score <= 70) AS needs_practice_topics,
                COUNT(*) FILTER (WHERE avg_score > 70) AS mastered_topics,
                AVG(avg_score) AS average_topic_mastery
            FROM topic_avg
            GROUP BY tenant_id
        ),
        student_totals AS (
            SELECT tenant_id, COUNT(DISTINCT user_id) AS active_learners
            FROM user_tenant_roles
            WHERE role = 'student'
            GROUP BY tenant_id
        ),
        completed_diagnostics AS (
            SELECT utr.tenant_id, COUNT(DISTINCT dt.user_id) AS completed_learners
            FROM diagnostic_tests dt
            JOIN user_tenant_roles utr ON utr.user_id = dt.user_id AND utr.role = 'student'
            WHERE dt.completed_at IS NOT NULL
            GROUP BY utr.tenant_id
        ),
        latest_roadmaps AS (
            SELECT r.user_id, MAX(r.id) AS roadmap_id
            FROM roadmaps r
            WHERE r.status IN ('ready', 'generating')
            GROUP BY r.user_id
        ),
        roadmap_totals AS (
            SELECT
                utr.tenant_id,
                COUNT(rs.id) AS total_steps,
                COUNT(*) FILTER (WHERE rs.progress_status = 'completed') AS completed_steps
            FROM latest_roadmaps lr
            JOIN roadmaps r ON r.id = lr.roadmap_id
            JOIN roadmap_steps rs ON rs.roadmap_id = r.id
            JOIN user_tenant_roles utr ON utr.user_id = r.user_id AND utr.role = 'student'
            GROUP BY utr.tenant_id
        ),
        weekly_events AS (
            SELECT tenant_id, COUNT(*) AS weekly_event_count
            FROM learning_events
            WHERE COALESCE(event_timestamp, created_at) >= NOW() - INTERVAL '7 days'
            GROUP BY tenant_id
        )
        SELECT
            t.id AS tenant_id,
            COALESCE(st.active_learners, 0) AS active_learners,
            COALESCE(we.weekly_event_count, 0) AS weekly_event_count,
            COALESCE(td.average_topic_mastery, 0) AS average_topic_mastery,
            CASE
                WHEN COALESCE(st.active_learners, 0) = 0 THEN 0
                ELSE ROUND((COALESCE(cd.completed_learners, 0)::numeric / st.active_learners::numeric) * 100, 2)
            END AS diagnostic_completion_rate,
            CASE
                WHEN COALESCE(rt.total_steps, 0) = 0 THEN 0
                ELSE ROUND((COALESCE(rt.completed_steps, 0)::numeric / rt.total_steps::numeric) * 100, 2)
            END AS roadmap_completion_rate,
            COALESCE(td.beginner_topics, 0) AS beginner_topics,
            COALESCE(td.needs_practice_topics, 0) AS needs_practice_topics,
            COALESCE(td.mastered_topics, 0) AS mastered_topics,
            NOW() AS refreshed_at
        FROM tenants t
        LEFT JOIN student_totals st ON st.tenant_id = t.id
        LEFT JOIN weekly_events we ON we.tenant_id = t.id
        LEFT JOIN completed_diagnostics cd ON cd.tenant_id = t.id
        LEFT JOIN roadmap_totals rt ON rt.tenant_id = t.id
        LEFT JOIN topic_distribution td ON td.tenant_id = t.id
        """
    )
    op.execute("CREATE UNIQUE INDEX ix_tenant_analytics_mv_tenant_id ON tenant_analytics_mv (tenant_id)")

    op.execute(
        """
        CREATE MATERIALIZED VIEW user_progress_summary_mv AS
        WITH latest_roadmaps AS (
            SELECT r.user_id, MAX(r.id) AS roadmap_id
            FROM roadmaps r
            WHERE r.status IN ('ready', 'generating')
            GROUP BY r.user_id
        ),
        latest_completed_tests AS (
            SELECT dt.user_id, MAX(dt.id) AS test_id
            FROM diagnostic_tests dt
            WHERE dt.completed_at IS NOT NULL
            GROUP BY dt.user_id
        ),
        weekly_events AS (
            SELECT
                tenant_id,
                user_id,
                COUNT(*) AS weekly_event_count
            FROM learning_events
            WHERE COALESCE(event_timestamp, created_at) >= NOW() - INTERVAL '7 days'
            GROUP BY tenant_id, user_id
        )
        SELECT
            utr.tenant_id,
            u.id AS user_id,
            u.email AS email,
            COUNT(rs.id) AS total_steps,
            COUNT(*) FILTER (WHERE rs.progress_status = 'completed') AS completed_steps,
            COUNT(*) FILTER (WHERE rs.progress_status = 'in_progress') AS in_progress_steps,
            COUNT(*) FILTER (WHERE rs.progress_status = 'pending') AS pending_steps,
            CASE
                WHEN COUNT(rs.id) = 0 THEN 0
                ELSE ROUND((COUNT(*) FILTER (WHERE rs.progress_status = 'completed')::numeric / COUNT(rs.id)::numeric) * 100)
            END AS completion_percent,
            CASE
                WHEN COUNT(rs.id) = 0 THEN 0
                ELSE ROUND((((COUNT(*) FILTER (WHERE rs.progress_status = 'completed') * 100)
                    + (COUNT(*) FILTER (WHERE rs.progress_status = 'in_progress') * 60)
                    + (COUNT(*) FILTER (WHERE rs.progress_status = 'pending') * 20))::numeric / COUNT(rs.id)::numeric))
            END AS mastery_percent,
            COALESCE(we.weekly_event_count, 0) AS weekly_event_count,
            COALESCE(AVG(ua.score), 0) AS average_score,
            NOW() AS refreshed_at
        FROM user_tenant_roles utr
        JOIN users u ON u.id = utr.user_id
        LEFT JOIN latest_roadmaps lr ON lr.user_id = u.id
        LEFT JOIN roadmaps r ON r.id = lr.roadmap_id
        LEFT JOIN roadmap_steps rs ON rs.roadmap_id = r.id
        LEFT JOIN latest_completed_tests lct ON lct.user_id = u.id
        LEFT JOIN user_answers ua ON ua.test_id = lct.test_id
        LEFT JOIN weekly_events we ON we.tenant_id = utr.tenant_id AND we.user_id = u.id
        WHERE utr.role = 'student'
        GROUP BY utr.tenant_id, u.id, u.email, we.weekly_event_count
        """
    )
    op.execute("CREATE UNIQUE INDEX ix_user_progress_summary_mv_tenant_user ON user_progress_summary_mv (tenant_id, user_id)")
    op.execute("CREATE INDEX ix_user_progress_summary_mv_tenant_mastery ON user_progress_summary_mv (tenant_id, mastery_percent DESC, completion_percent DESC)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_user_progress_summary_mv_tenant_mastery")
    op.execute("DROP INDEX IF EXISTS ix_user_progress_summary_mv_tenant_user")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS user_progress_summary_mv")
    op.execute("DROP INDEX IF EXISTS ix_tenant_analytics_mv_tenant_id")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS tenant_analytics_mv")
