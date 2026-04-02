-- Phase 2 tenant RLS rollout.
-- Assumes app_security.current_tenant_id/current_role/current_user_id and
-- app_security.tenant_match/tenant_match_or_global already exist.
--
-- This script is intentionally additive:
-- - it does not remove repository-side tenant filters
-- - it adds missing RLS policies so database enforcement catches missed filters

create or replace function app_security.apply_simple_tenant_rls(target_table text)
returns void
language plpgsql
as $$
begin
    execute format('alter table %I enable row level security', target_table);
    execute format('alter table %I force row level security', target_table);

    execute format('drop policy if exists %I_tenant_select on %I', target_table, target_table);
    execute format('drop policy if exists %I_tenant_insert on %I', target_table, target_table);
    execute format('drop policy if exists %I_tenant_update on %I', target_table, target_table);
    execute format('drop policy if exists %I_tenant_delete on %I', target_table, target_table);

    execute format(
        'create policy %I_tenant_select on %I for select using (app_security.tenant_match(tenant_id))',
        target_table,
        target_table
    );
    execute format(
        'create policy %I_tenant_insert on %I for insert with check (app_security.tenant_match(tenant_id))',
        target_table,
        target_table
    );
    execute format(
        'create policy %I_tenant_update on %I for update using (app_security.tenant_match(tenant_id)) with check (app_security.tenant_match(tenant_id))',
        target_table,
        target_table
    );
    execute format(
        'create policy %I_tenant_delete on %I for delete using (app_security.tenant_match(tenant_id))',
        target_table,
        target_table
    );
end;
$$;

-- Direct tenant tables with required tenant_id.
select app_security.apply_simple_tenant_rls('ai_requests');
select app_security.apply_simple_tenant_rls('api_clients');
select app_security.apply_simple_tenant_rls('auth_logs');
select app_security.apply_simple_tenant_rls('auth_tokens');
select app_security.apply_simple_tenant_rls('badges');
select app_security.apply_simple_tenant_rls('diagnostic_test_states');
select app_security.apply_simple_tenant_rls('experiments');
select app_security.apply_simple_tenant_rls('gamification_events');
select app_security.apply_simple_tenant_rls('gamification_profiles');
select app_security.apply_simple_tenant_rls('marketplace_reviews');
select app_security.apply_simple_tenant_rls('mentor_memory_profiles');
select app_security.apply_simple_tenant_rls('mentor_session_memories');
select app_security.apply_simple_tenant_rls('mentor_students');
select app_security.apply_simple_tenant_rls('ml_feature_snapshots');
select app_security.apply_simple_tenant_rls('ml_model_registry');
select app_security.apply_simple_tenant_rls('ml_training_runs');
select app_security.apply_simple_tenant_rls('plugin_registry');
select app_security.apply_simple_tenant_rls('refresh_tokens');
select app_security.apply_simple_tenant_rls('sessions');
select app_security.apply_simple_tenant_rls('social_follows');
select app_security.apply_simple_tenant_rls('tenant_subscriptions');
select app_security.apply_simple_tenant_rls('topic_features');
select app_security.apply_simple_tenant_rls('user_features');
select app_security.apply_simple_tenant_rls('user_skill_vectors');
select app_security.apply_simple_tenant_rls('user_tenant_roles');

-- Direct tenant tables that may intentionally allow global/null tenant rows.
create or replace function app_security.apply_tenant_or_global_rls(target_table text)
returns void
language plpgsql
as $$
begin
    execute format('alter table %I enable row level security', target_table);
    execute format('alter table %I force row level security', target_table);

    execute format('drop policy if exists %I_tenant_select on %I', target_table, target_table);
    execute format('drop policy if exists %I_tenant_insert on %I', target_table, target_table);
    execute format('drop policy if exists %I_tenant_update on %I', target_table, target_table);
    execute format('drop policy if exists %I_tenant_delete on %I', target_table, target_table);

    execute format(
        'create policy %I_tenant_select on %I for select using (app_security.tenant_match_or_global(tenant_id))',
        target_table,
        target_table
    );
    execute format(
        'create policy %I_tenant_insert on %I for insert with check (app_security.tenant_match_or_global(tenant_id))',
        target_table,
        target_table
    );
    execute format(
        'create policy %I_tenant_update on %I for update using (app_security.tenant_match_or_global(tenant_id)) with check (app_security.tenant_match_or_global(tenant_id))',
        target_table,
        target_table
    );
    execute format(
        'create policy %I_tenant_delete on %I for delete using (app_security.tenant_match_or_global(tenant_id))',
        target_table,
        target_table
    );
end;
$$;

-- Apply only to tables where null tenant rows are intentional shared/global data.
select app_security.apply_tenant_or_global_rls('audit_logs');
select app_security.apply_tenant_or_global_rls('authorization_policies');
select app_security.apply_tenant_or_global_rls('content_metadata');
select app_security.apply_tenant_or_global_rls('feature_flags');
select app_security.apply_tenant_or_global_rls('file_assets');
select app_security.apply_tenant_or_global_rls('job_roles');
select app_security.apply_tenant_or_global_rls('marketplace_listings');
select app_security.apply_tenant_or_global_rls('mentor_chat_messages');
select app_security.apply_tenant_or_global_rls('mentor_messages');
select app_security.apply_tenant_or_global_rls('mentor_suggestions');
select app_security.apply_tenant_or_global_rls('resources');
select app_security.apply_tenant_or_global_rls('skills');
select app_security.apply_tenant_or_global_rls('subscription_plans');
select app_security.apply_tenant_or_global_rls('token_blacklist');

-- Derived tenant tables.

alter table user_answers enable row level security;
alter table user_answers force row level security;
drop policy if exists user_answers_tenant_select on user_answers;
drop policy if exists user_answers_tenant_insert on user_answers;
drop policy if exists user_answers_tenant_update on user_answers;
drop policy if exists user_answers_tenant_delete on user_answers;
create policy user_answers_tenant_select on user_answers
for select using (
    app_security.is_super_admin()
    or exists (
        select 1
        from diagnostic_tests dt
        join users u on u.id = dt.user_id
        where dt.id = user_answers.test_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy user_answers_tenant_insert on user_answers
for insert with check (
    app_security.is_super_admin()
    or exists (
        select 1
        from diagnostic_tests dt
        join users u on u.id = dt.user_id
        where dt.id = user_answers.test_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy user_answers_tenant_update on user_answers
for update using (
    app_security.is_super_admin()
    or exists (
        select 1
        from diagnostic_tests dt
        join users u on u.id = dt.user_id
        where dt.id = user_answers.test_id
          and app_security.tenant_match(u.tenant_id)
    )
) with check (
    app_security.is_super_admin()
    or exists (
        select 1
        from diagnostic_tests dt
        join users u on u.id = dt.user_id
        where dt.id = user_answers.test_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy user_answers_tenant_delete on user_answers
for delete using (
    app_security.is_super_admin()
    or exists (
        select 1
        from diagnostic_tests dt
        join users u on u.id = dt.user_id
        where dt.id = user_answers.test_id
          and app_security.tenant_match(u.tenant_id)
    )
);

alter table refresh_sessions enable row level security;
alter table refresh_sessions force row level security;
drop policy if exists refresh_sessions_tenant_select on refresh_sessions;
drop policy if exists refresh_sessions_tenant_insert on refresh_sessions;
drop policy if exists refresh_sessions_tenant_update on refresh_sessions;
drop policy if exists refresh_sessions_tenant_delete on refresh_sessions;
create policy refresh_sessions_tenant_select on refresh_sessions
for select using (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = refresh_sessions.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy refresh_sessions_tenant_insert on refresh_sessions
for insert with check (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = refresh_sessions.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy refresh_sessions_tenant_update on refresh_sessions
for update using (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = refresh_sessions.user_id
          and app_security.tenant_match(u.tenant_id)
    )
) with check (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = refresh_sessions.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy refresh_sessions_tenant_delete on refresh_sessions
for delete using (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = refresh_sessions.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);

alter table goal_topics enable row level security;
alter table goal_topics force row level security;
drop policy if exists goal_topics_tenant_select on goal_topics;
drop policy if exists goal_topics_tenant_insert on goal_topics;
drop policy if exists goal_topics_tenant_update on goal_topics;
drop policy if exists goal_topics_tenant_delete on goal_topics;
create policy goal_topics_tenant_select on goal_topics
for select using (
    app_security.is_super_admin()
    or exists (
        select 1
        from goals g
        join topics t on t.id = goal_topics.topic_id
        where g.id = goal_topics.goal_id
          and app_security.tenant_match(g.tenant_id)
          and t.tenant_id = g.tenant_id
    )
);
create policy goal_topics_tenant_insert on goal_topics
for insert with check (
    app_security.is_super_admin()
    or exists (
        select 1
        from goals g
        join topics t on t.id = goal_topics.topic_id
        where g.id = goal_topics.goal_id
          and app_security.tenant_match(g.tenant_id)
          and t.tenant_id = g.tenant_id
    )
);
create policy goal_topics_tenant_update on goal_topics
for update using (
    app_security.is_super_admin()
    or exists (
        select 1
        from goals g
        join topics t on t.id = goal_topics.topic_id
        where g.id = goal_topics.goal_id
          and app_security.tenant_match(g.tenant_id)
          and t.tenant_id = g.tenant_id
    )
) with check (
    app_security.is_super_admin()
    or exists (
        select 1
        from goals g
        join topics t on t.id = goal_topics.topic_id
        where g.id = goal_topics.goal_id
          and app_security.tenant_match(g.tenant_id)
          and t.tenant_id = g.tenant_id
    )
);
create policy goal_topics_tenant_delete on goal_topics
for delete using (
    app_security.is_super_admin()
    or exists (
        select 1
        from goals g
        join topics t on t.id = goal_topics.topic_id
        where g.id = goal_topics.goal_id
          and app_security.tenant_match(g.tenant_id)
          and t.tenant_id = g.tenant_id
    )
);

alter table topic_prerequisites enable row level security;
alter table topic_prerequisites force row level security;
drop policy if exists topic_prerequisites_tenant_select on topic_prerequisites;
drop policy if exists topic_prerequisites_tenant_insert on topic_prerequisites;
drop policy if exists topic_prerequisites_tenant_update on topic_prerequisites;
drop policy if exists topic_prerequisites_tenant_delete on topic_prerequisites;
create policy topic_prerequisites_tenant_select on topic_prerequisites
for select using (
    app_security.is_super_admin()
    or exists (
        select 1
        from topics t
        join topics p on p.id = topic_prerequisites.prerequisite_topic_id
        where t.id = topic_prerequisites.topic_id
          and app_security.tenant_match(t.tenant_id)
          and p.tenant_id = t.tenant_id
    )
);
create policy topic_prerequisites_tenant_insert on topic_prerequisites
for insert with check (
    app_security.is_super_admin()
    or exists (
        select 1
        from topics t
        join topics p on p.id = topic_prerequisites.prerequisite_topic_id
        where t.id = topic_prerequisites.topic_id
          and app_security.tenant_match(t.tenant_id)
          and p.tenant_id = t.tenant_id
    )
);
create policy topic_prerequisites_tenant_update on topic_prerequisites
for update using (
    app_security.is_super_admin()
    or exists (
        select 1
        from topics t
        join topics p on p.id = topic_prerequisites.prerequisite_topic_id
        where t.id = topic_prerequisites.topic_id
          and app_security.tenant_match(t.tenant_id)
          and p.tenant_id = t.tenant_id
    )
) with check (
    app_security.is_super_admin()
    or exists (
        select 1
        from topics t
        join topics p on p.id = topic_prerequisites.prerequisite_topic_id
        where t.id = topic_prerequisites.topic_id
          and app_security.tenant_match(t.tenant_id)
          and p.tenant_id = t.tenant_id
    )
);
create policy topic_prerequisites_tenant_delete on topic_prerequisites
for delete using (
    app_security.is_super_admin()
    or exists (
        select 1
        from topics t
        join topics p on p.id = topic_prerequisites.prerequisite_topic_id
        where t.id = topic_prerequisites.topic_id
          and app_security.tenant_match(t.tenant_id)
          and p.tenant_id = t.tenant_id
    )
);

alter table topic_skills enable row level security;
alter table topic_skills force row level security;
drop policy if exists topic_skills_tenant_select on topic_skills;
drop policy if exists topic_skills_tenant_insert on topic_skills;
drop policy if exists topic_skills_tenant_update on topic_skills;
drop policy if exists topic_skills_tenant_delete on topic_skills;
create policy topic_skills_tenant_select on topic_skills
for select using (
    app_security.is_super_admin()
    or exists (
        select 1
        from topics t
        join skills s on s.id = topic_skills.skill_id
        where t.id = topic_skills.topic_id
          and app_security.tenant_match(t.tenant_id)
          and (s.tenant_id = t.tenant_id or s.tenant_id is null)
    )
);
create policy topic_skills_tenant_insert on topic_skills
for insert with check (
    app_security.is_super_admin()
    or exists (
        select 1
        from topics t
        join skills s on s.id = topic_skills.skill_id
        where t.id = topic_skills.topic_id
          and app_security.tenant_match(t.tenant_id)
          and (s.tenant_id = t.tenant_id or s.tenant_id is null)
    )
);
create policy topic_skills_tenant_update on topic_skills
for update using (
    app_security.is_super_admin()
    or exists (
        select 1
        from topics t
        join skills s on s.id = topic_skills.skill_id
        where t.id = topic_skills.topic_id
          and app_security.tenant_match(t.tenant_id)
          and (s.tenant_id = t.tenant_id or s.tenant_id is null)
    )
) with check (
    app_security.is_super_admin()
    or exists (
        select 1
        from topics t
        join skills s on s.id = topic_skills.skill_id
        where t.id = topic_skills.topic_id
          and app_security.tenant_match(t.tenant_id)
          and (s.tenant_id = t.tenant_id or s.tenant_id is null)
    )
);
create policy topic_skills_tenant_delete on topic_skills
for delete using (
    app_security.is_super_admin()
    or exists (
        select 1
        from topics t
        join skills s on s.id = topic_skills.skill_id
        where t.id = topic_skills.topic_id
          and app_security.tenant_match(t.tenant_id)
          and (s.tenant_id = t.tenant_id or s.tenant_id is null)
    )
);

alter table job_role_skills enable row level security;
alter table job_role_skills force row level security;
drop policy if exists job_role_skills_tenant_select on job_role_skills;
drop policy if exists job_role_skills_tenant_insert on job_role_skills;
drop policy if exists job_role_skills_tenant_update on job_role_skills;
drop policy if exists job_role_skills_tenant_delete on job_role_skills;
create policy job_role_skills_tenant_select on job_role_skills
for select using (
    app_security.is_super_admin()
    or exists (
        select 1
        from job_roles jr
        join skills s on s.id = job_role_skills.skill_id
        where jr.id = job_role_skills.job_role_id
          and app_security.tenant_match_or_global(jr.tenant_id)
          and (s.tenant_id = jr.tenant_id or s.tenant_id is null)
    )
);
create policy job_role_skills_tenant_insert on job_role_skills
for insert with check (
    app_security.is_super_admin()
    or exists (
        select 1
        from job_roles jr
        join skills s on s.id = job_role_skills.skill_id
        where jr.id = job_role_skills.job_role_id
          and app_security.tenant_match_or_global(jr.tenant_id)
          and (s.tenant_id = jr.tenant_id or s.tenant_id is null)
    )
);
create policy job_role_skills_tenant_update on job_role_skills
for update using (
    app_security.is_super_admin()
    or exists (
        select 1
        from job_roles jr
        join skills s on s.id = job_role_skills.skill_id
        where jr.id = job_role_skills.job_role_id
          and app_security.tenant_match_or_global(jr.tenant_id)
          and (s.tenant_id = jr.tenant_id or s.tenant_id is null)
    )
) with check (
    app_security.is_super_admin()
    or exists (
        select 1
        from job_roles jr
        join skills s on s.id = job_role_skills.skill_id
        where jr.id = job_role_skills.job_role_id
          and app_security.tenant_match_or_global(jr.tenant_id)
          and (s.tenant_id = jr.tenant_id or s.tenant_id is null)
    )
);
create policy job_role_skills_tenant_delete on job_role_skills
for delete using (
    app_security.is_super_admin()
    or exists (
        select 1
        from job_roles jr
        join skills s on s.id = job_role_skills.skill_id
        where jr.id = job_role_skills.job_role_id
          and app_security.tenant_match_or_global(jr.tenant_id)
          and (s.tenant_id = jr.tenant_id or s.tenant_id is null)
    )
);

alter table experiment_variants enable row level security;
alter table experiment_variants force row level security;
drop policy if exists experiment_variants_tenant_select on experiment_variants;
drop policy if exists experiment_variants_tenant_insert on experiment_variants;
drop policy if exists experiment_variants_tenant_update on experiment_variants;
drop policy if exists experiment_variants_tenant_delete on experiment_variants;
create policy experiment_variants_tenant_select on experiment_variants
for select using (
    app_security.is_super_admin()
    or exists (
        select 1 from experiments e
        where e.id = experiment_variants.experiment_id
          and app_security.tenant_match(e.tenant_id)
    )
);
create policy experiment_variants_tenant_insert on experiment_variants
for insert with check (
    app_security.is_super_admin()
    or exists (
        select 1 from experiments e
        where e.id = experiment_variants.experiment_id
          and app_security.tenant_match(e.tenant_id)
    )
);
create policy experiment_variants_tenant_update on experiment_variants
for update using (
    app_security.is_super_admin()
    or exists (
        select 1 from experiments e
        where e.id = experiment_variants.experiment_id
          and app_security.tenant_match(e.tenant_id)
    )
) with check (
    app_security.is_super_admin()
    or exists (
        select 1 from experiments e
        where e.id = experiment_variants.experiment_id
          and app_security.tenant_match(e.tenant_id)
    )
);
create policy experiment_variants_tenant_delete on experiment_variants
for delete using (
    app_security.is_super_admin()
    or exists (
        select 1 from experiments e
        where e.id = experiment_variants.experiment_id
          and app_security.tenant_match(e.tenant_id)
    )
);

-- Shared operational tables are intentionally excluded here:
-- - outbox_events
-- - dead_letter_events
-- - processed_stream_events
-- - event_consumer_states
-- - stream_consumer_offsets
--
-- Roll those out only after every consumer/worker path is audited, because
-- some of them are intentionally cross-tenant operational data.
