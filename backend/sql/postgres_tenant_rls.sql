create schema if not exists app_security;

create or replace function app_security.current_tenant_id()
returns integer
language sql
stable
as $$
    select nullif(current_setting('app.current_tenant_id', true), '')::integer
$$;

create or replace function app_security.current_role()
returns text
language sql
stable
as $$
    select coalesce(nullif(current_setting('app.current_role', true), ''), 'anonymous')
$$;

create or replace function app_security.current_user_id()
returns integer
language sql
stable
as $$
    select nullif(current_setting('app.current_user_id', true), '')::integer
$$;

create or replace function app_security.is_super_admin()
returns boolean
language sql
stable
as $$
    select app_security.current_role() = 'super_admin'
$$;

create or replace function app_security.tenant_match(target_tenant_id integer)
returns boolean
language sql
stable
as $$
    select app_security.is_super_admin()
        or (
            app_security.current_tenant_id() is not null
            and target_tenant_id = app_security.current_tenant_id()
        )
$$;

create or replace function app_security.tenant_match_or_global(target_tenant_id integer)
returns boolean
language sql
stable
as $$
    select app_security.is_super_admin()
        or target_tenant_id is null
        or (
            app_security.current_tenant_id() is not null
            and target_tenant_id = app_security.current_tenant_id()
        )
$$;

alter table users enable row level security;
alter table users force row level security;
drop policy if exists users_tenant_select on users;
drop policy if exists users_tenant_insert on users;
drop policy if exists users_tenant_update on users;
drop policy if exists users_tenant_delete on users;
create policy users_tenant_select on users for select using (app_security.tenant_match(tenant_id));
create policy users_tenant_insert on users for insert with check (app_security.tenant_match(tenant_id));
create policy users_tenant_update on users for update using (app_security.tenant_match(tenant_id)) with check (app_security.tenant_match(tenant_id));
create policy users_tenant_delete on users for delete using (app_security.tenant_match(tenant_id));

alter table topics enable row level security;
alter table topics force row level security;
drop policy if exists topics_tenant_select on topics;
drop policy if exists topics_tenant_insert on topics;
drop policy if exists topics_tenant_update on topics;
drop policy if exists topics_tenant_delete on topics;
create policy topics_tenant_select on topics for select using (app_security.tenant_match(tenant_id));
create policy topics_tenant_insert on topics for insert with check (app_security.tenant_match(tenant_id));
create policy topics_tenant_update on topics for update using (app_security.tenant_match(tenant_id)) with check (app_security.tenant_match(tenant_id));
create policy topics_tenant_delete on topics for delete using (app_security.tenant_match(tenant_id));

alter table goals enable row level security;
alter table goals force row level security;
drop policy if exists goals_tenant_select on goals;
drop policy if exists goals_tenant_insert on goals;
drop policy if exists goals_tenant_update on goals;
drop policy if exists goals_tenant_delete on goals;
create policy goals_tenant_select on goals for select using (app_security.tenant_match(tenant_id));
create policy goals_tenant_insert on goals for insert with check (app_security.tenant_match(tenant_id));
create policy goals_tenant_update on goals for update using (app_security.tenant_match(tenant_id)) with check (app_security.tenant_match(tenant_id));
create policy goals_tenant_delete on goals for delete using (app_security.tenant_match(tenant_id));

alter table roadmaps enable row level security;
alter table roadmaps force row level security;
drop policy if exists roadmaps_tenant_select on roadmaps;
drop policy if exists roadmaps_tenant_insert on roadmaps;
drop policy if exists roadmaps_tenant_update on roadmaps;
drop policy if exists roadmaps_tenant_delete on roadmaps;
create policy roadmaps_tenant_select on roadmaps
for select using (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = roadmaps.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy roadmaps_tenant_insert on roadmaps
for insert with check (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = roadmaps.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy roadmaps_tenant_update on roadmaps
for update using (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = roadmaps.user_id
          and app_security.tenant_match(u.tenant_id)
    )
) with check (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = roadmaps.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy roadmaps_tenant_delete on roadmaps
for delete using (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = roadmaps.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);

alter table communities enable row level security;
alter table communities force row level security;
drop policy if exists communities_tenant_select on communities;
drop policy if exists communities_tenant_insert on communities;
drop policy if exists communities_tenant_update on communities;
drop policy if exists communities_tenant_delete on communities;
create policy communities_tenant_select on communities for select using (app_security.tenant_match(tenant_id));
create policy communities_tenant_insert on communities for insert with check (app_security.tenant_match(tenant_id));
create policy communities_tenant_update on communities for update using (app_security.tenant_match(tenant_id)) with check (app_security.tenant_match(tenant_id));
create policy communities_tenant_delete on communities for delete using (app_security.tenant_match(tenant_id));

alter table community_members enable row level security;
alter table community_members force row level security;
drop policy if exists community_members_tenant_select on community_members;
drop policy if exists community_members_tenant_insert on community_members;
drop policy if exists community_members_tenant_update on community_members;
drop policy if exists community_members_tenant_delete on community_members;
create policy community_members_tenant_select on community_members for select using (app_security.tenant_match(tenant_id));
create policy community_members_tenant_insert on community_members for insert with check (app_security.tenant_match(tenant_id));
create policy community_members_tenant_update on community_members for update using (app_security.tenant_match(tenant_id)) with check (app_security.tenant_match(tenant_id));
create policy community_members_tenant_delete on community_members for delete using (app_security.tenant_match(tenant_id));

alter table discussion_threads enable row level security;
alter table discussion_threads force row level security;
drop policy if exists discussion_threads_tenant_select on discussion_threads;
drop policy if exists discussion_threads_tenant_insert on discussion_threads;
drop policy if exists discussion_threads_tenant_update on discussion_threads;
drop policy if exists discussion_threads_tenant_delete on discussion_threads;
create policy discussion_threads_tenant_select on discussion_threads for select using (app_security.tenant_match(tenant_id));
create policy discussion_threads_tenant_insert on discussion_threads for insert with check (app_security.tenant_match(tenant_id));
create policy discussion_threads_tenant_update on discussion_threads for update using (app_security.tenant_match(tenant_id)) with check (app_security.tenant_match(tenant_id));
create policy discussion_threads_tenant_delete on discussion_threads for delete using (app_security.tenant_match(tenant_id));

alter table discussion_replies enable row level security;
alter table discussion_replies force row level security;
drop policy if exists discussion_replies_tenant_select on discussion_replies;
drop policy if exists discussion_replies_tenant_insert on discussion_replies;
drop policy if exists discussion_replies_tenant_update on discussion_replies;
drop policy if exists discussion_replies_tenant_delete on discussion_replies;
create policy discussion_replies_tenant_select on discussion_replies for select using (app_security.tenant_match(tenant_id));
create policy discussion_replies_tenant_insert on discussion_replies for insert with check (app_security.tenant_match(tenant_id));
create policy discussion_replies_tenant_update on discussion_replies for update using (app_security.tenant_match(tenant_id)) with check (app_security.tenant_match(tenant_id));
create policy discussion_replies_tenant_delete on discussion_replies for delete using (app_security.tenant_match(tenant_id));

alter table analytics_snapshots enable row level security;
alter table analytics_snapshots force row level security;
drop policy if exists analytics_snapshots_tenant_select on analytics_snapshots;
drop policy if exists analytics_snapshots_tenant_insert on analytics_snapshots;
drop policy if exists analytics_snapshots_tenant_update on analytics_snapshots;
drop policy if exists analytics_snapshots_tenant_delete on analytics_snapshots;
create policy analytics_snapshots_tenant_select on analytics_snapshots for select using (app_security.tenant_match_or_global(tenant_id));
create policy analytics_snapshots_tenant_insert on analytics_snapshots for insert with check (app_security.tenant_match_or_global(tenant_id));
create policy analytics_snapshots_tenant_update on analytics_snapshots for update using (app_security.tenant_match_or_global(tenant_id)) with check (app_security.tenant_match_or_global(tenant_id));
create policy analytics_snapshots_tenant_delete on analytics_snapshots for delete using (app_security.tenant_match_or_global(tenant_id));

alter table learning_events enable row level security;
alter table learning_events force row level security;
drop policy if exists learning_events_tenant_select on learning_events;
drop policy if exists learning_events_tenant_insert on learning_events;
drop policy if exists learning_events_tenant_update on learning_events;
drop policy if exists learning_events_tenant_delete on learning_events;
create policy learning_events_tenant_select on learning_events for select using (app_security.tenant_match(tenant_id));
create policy learning_events_tenant_insert on learning_events for insert with check (app_security.tenant_match(tenant_id));
create policy learning_events_tenant_update on learning_events for update using (app_security.tenant_match(tenant_id)) with check (app_security.tenant_match(tenant_id));
create policy learning_events_tenant_delete on learning_events for delete using (app_security.tenant_match(tenant_id));

alter table notifications enable row level security;
alter table notifications force row level security;
drop policy if exists notifications_tenant_select on notifications;
drop policy if exists notifications_tenant_insert on notifications;
drop policy if exists notifications_tenant_update on notifications;
drop policy if exists notifications_tenant_delete on notifications;
create policy notifications_tenant_select on notifications for select using (app_security.tenant_match(tenant_id));
create policy notifications_tenant_insert on notifications for insert with check (app_security.tenant_match(tenant_id));
create policy notifications_tenant_update on notifications for update using (app_security.tenant_match(tenant_id)) with check (app_security.tenant_match(tenant_id));
create policy notifications_tenant_delete on notifications for delete using (app_security.tenant_match(tenant_id));

alter table topic_scores enable row level security;
alter table topic_scores force row level security;
drop policy if exists topic_scores_tenant_select on topic_scores;
drop policy if exists topic_scores_tenant_insert on topic_scores;
drop policy if exists topic_scores_tenant_update on topic_scores;
drop policy if exists topic_scores_tenant_delete on topic_scores;
create policy topic_scores_tenant_select on topic_scores for select using (app_security.tenant_match(tenant_id));
create policy topic_scores_tenant_insert on topic_scores for insert with check (app_security.tenant_match(tenant_id));
create policy topic_scores_tenant_update on topic_scores for update using (app_security.tenant_match(tenant_id)) with check (app_security.tenant_match(tenant_id));
create policy topic_scores_tenant_delete on topic_scores for delete using (app_security.tenant_match(tenant_id));

alter table questions enable row level security;
alter table questions force row level security;
drop policy if exists questions_tenant_select on questions;
drop policy if exists questions_tenant_insert on questions;
drop policy if exists questions_tenant_update on questions;
drop policy if exists questions_tenant_delete on questions;
create policy questions_tenant_select on questions
for select using (
    app_security.is_super_admin()
    or exists (
        select 1 from topics t
        where t.id = questions.topic_id
          and app_security.tenant_match(t.tenant_id)
    )
);
create policy questions_tenant_insert on questions
for insert with check (
    app_security.is_super_admin()
    or exists (
        select 1 from topics t
        where t.id = questions.topic_id
          and app_security.tenant_match(t.tenant_id)
    )
);
create policy questions_tenant_update on questions
for update using (
    app_security.is_super_admin()
    or exists (
        select 1 from topics t
        where t.id = questions.topic_id
          and app_security.tenant_match(t.tenant_id)
    )
) with check (
    app_security.is_super_admin()
    or exists (
        select 1 from topics t
        where t.id = questions.topic_id
          and app_security.tenant_match(t.tenant_id)
    )
);
create policy questions_tenant_delete on questions
for delete using (
    app_security.is_super_admin()
    or exists (
        select 1 from topics t
        where t.id = questions.topic_id
          and app_security.tenant_match(t.tenant_id)
    )
);

alter table roadmap_steps enable row level security;
alter table roadmap_steps force row level security;
drop policy if exists roadmap_steps_tenant_select on roadmap_steps;
drop policy if exists roadmap_steps_tenant_insert on roadmap_steps;
drop policy if exists roadmap_steps_tenant_update on roadmap_steps;
drop policy if exists roadmap_steps_tenant_delete on roadmap_steps;
create policy roadmap_steps_tenant_select on roadmap_steps
for select using (
    app_security.is_super_admin()
    or exists (
        select 1 from roadmaps r
        join users u on u.id = r.user_id
        where r.id = roadmap_steps.roadmap_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy roadmap_steps_tenant_insert on roadmap_steps
for insert with check (
    app_security.is_super_admin()
    or exists (
        select 1 from roadmaps r
        join users u on u.id = r.user_id
        where r.id = roadmap_steps.roadmap_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy roadmap_steps_tenant_update on roadmap_steps
for update using (
    app_security.is_super_admin()
    or exists (
        select 1 from roadmaps r
        join users u on u.id = r.user_id
        where r.id = roadmap_steps.roadmap_id
          and app_security.tenant_match(u.tenant_id)
    )
) with check (
    app_security.is_super_admin()
    or exists (
        select 1 from roadmaps r
        join users u on u.id = r.user_id
        where r.id = roadmap_steps.roadmap_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy roadmap_steps_tenant_delete on roadmap_steps
for delete using (
    app_security.is_super_admin()
    or exists (
        select 1 from roadmaps r
        join users u on u.id = r.user_id
        where r.id = roadmap_steps.roadmap_id
          and app_security.tenant_match(u.tenant_id)
    )
);

alter table diagnostic_tests enable row level security;
alter table diagnostic_tests force row level security;
drop policy if exists diagnostic_tests_tenant_select on diagnostic_tests;
drop policy if exists diagnostic_tests_tenant_insert on diagnostic_tests;
drop policy if exists diagnostic_tests_tenant_update on diagnostic_tests;
drop policy if exists diagnostic_tests_tenant_delete on diagnostic_tests;
create policy diagnostic_tests_tenant_select on diagnostic_tests
for select using (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = diagnostic_tests.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy diagnostic_tests_tenant_insert on diagnostic_tests
for insert with check (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = diagnostic_tests.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy diagnostic_tests_tenant_update on diagnostic_tests
for update using (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = diagnostic_tests.user_id
          and app_security.tenant_match(u.tenant_id)
    )
) with check (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = diagnostic_tests.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);
create policy diagnostic_tests_tenant_delete on diagnostic_tests
for delete using (
    app_security.is_super_admin()
    or exists (
        select 1 from users u
        where u.id = diagnostic_tests.user_id
          and app_security.tenant_match(u.tenant_id)
    )
);
