from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from random import Random

from sqlalchemy import select

from app.core.security import hash_password, verify_password
from app.domain.models.badge import Badge
from app.domain.models.community import Community
from app.domain.models.community_member import CommunityMember
from app.domain.models.diagnostic_test import DiagnosticTest
from app.domain.models.discussion_reply import DiscussionReply
from app.domain.models.discussion_thread import DiscussionThread
from app.domain.models.experiment import Experiment
from app.domain.models.experiment_variant import ExperimentVariant
from app.domain.models.goal import Goal
from app.domain.models.goal_topic import GoalTopic
from app.domain.models.learning_event import LearningEvent
from app.domain.models.mentor_suggestion import MentorSuggestion
from app.domain.models.question import Question
from app.domain.models.roadmap import Roadmap
from app.domain.models.roadmap_step import RoadmapStep
from app.domain.models.tenant import Tenant, TenantType
from app.domain.models.topic import Topic
from app.domain.models.topic_prerequisite import TopicPrerequisite
from app.domain.models.topic_score import TopicScore
from app.domain.models.user import User, UserRole
from app.domain.models.user_answer import UserAnswer
from app.infrastructure.database import AsyncSessionLocal
from scripts.demo_data_factory import build_demo_tenants, build_goal_topic_names


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


PLATFORM_SUPER_ADMIN = {
    "label": "Super Admin Panel",
    "email": "superadmin@platform.example.com",
    "password": "SuperAdmin123!",
    "role": UserRole.super_admin,
}

LEARNING_EVENT_TYPES = [
    "study_session",
    "practice_quiz",
    "topic_review",
    "mentor_checkin",
    "roadmap_step_completed",
    "discussion_reply",
]

BADGE_LIBRARY = [
    ("Consistency Starter", "Maintained a meaningful learning streak.", "streak"),
    ("Focus Finisher", "Closed a high-priority roadmap step.", "roadmap"),
    ("Community Helper", "Contributed useful help in the community.", "community"),
    ("Insight Builder", "Turned activity into a clear reflective takeaway.", "reflection"),
]


async def _get_or_create_tenant(session, *, name: str, tenant_type: TenantType) -> Tenant:
    tenant = (await session.execute(select(Tenant).where(Tenant.name == name))).scalar_one_or_none()
    if tenant is None:
        tenant = Tenant(name=name, type=tenant_type, created_at=_utcnow())
        session.add(tenant)
        await session.flush()
    return tenant


async def _ensure_user(session, *, tenant: Tenant, email: str, password: str, role: UserRole, display_name: str | None = None) -> User:
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        user = User(
            tenant_id=tenant.id,
            email=email,
            display_name=display_name,
            password_hash=hash_password(password),
            role=role,
            created_at=_utcnow() - timedelta(days=Random(email).randint(40, 300)),
        )
        session.add(user)
        await session.flush()
        return user

    if user.tenant_id != tenant.id:
        user.tenant_id = tenant.id
    if user.role != role:
        user.role = role
    if display_name:
        user.display_name = display_name
    if not verify_password(password, user.password_hash):
        user.password_hash = hash_password(password)
    return user


async def _seed_platform_super_admin(session) -> tuple[Tenant, dict]:
    tenant = await _get_or_create_tenant(session, name="Platform", tenant_type=TenantType.platform)
    await _ensure_user(
        session,
        tenant=tenant,
        email=PLATFORM_SUPER_ADMIN["email"],
        password=PLATFORM_SUPER_ADMIN["password"],
        role=PLATFORM_SUPER_ADMIN["role"],
        display_name="Platform Super Admin",
    )
    return tenant, PLATFORM_SUPER_ADMIN


async def _seed_topics(session, *, tenant: Tenant, topic_specs: list[dict]) -> dict[str, Topic]:
    rows: dict[str, Topic] = {}
    for topic_spec in topic_specs:
        topic = (
            await session.execute(select(Topic).where(Topic.tenant_id == tenant.id, Topic.name == topic_spec["name"]))
        ).scalar_one_or_none()
        if topic is None:
            topic = Topic(tenant_id=tenant.id, name=topic_spec["name"], description=topic_spec["description"])
            session.add(topic)
            await session.flush()
        else:
            topic.description = topic_spec["description"]
        rows[topic.name] = topic

        for question_spec in topic_spec["questions"]:
            existing = (
                await session.execute(
                    select(Question).where(Question.topic_id == topic.id, Question.question_text == question_spec["question_text"])
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    Question(
                        topic_id=topic.id,
                        difficulty=question_spec["difficulty"],
                        question_type=question_spec["question_type"],
                        question_text=question_spec["question_text"],
                        correct_answer=question_spec["correct_answer"],
                        accepted_answers=question_spec["accepted_answers"],
                        answer_options=question_spec["answer_options"],
                    )
                )
    await session.flush()
    return rows


async def _seed_goals(session, *, tenant: Tenant, goal_specs: list[dict], topic_rows: dict[str, Topic]) -> dict[str, Goal]:
    goals: dict[str, Goal] = {}
    topic_names = list(topic_rows.keys())
    topic_groups = build_goal_topic_names(topic_names, len(goal_specs), rng=Random(f"goals-{tenant.name}"))
    for goal_spec, selected_topics in zip(goal_specs, topic_groups, strict=False):
        goal = (
            await session.execute(select(Goal).where(Goal.tenant_id == tenant.id, Goal.name == goal_spec["name"]))
        ).scalar_one_or_none()
        if goal is None:
            goal = Goal(tenant_id=tenant.id, name=goal_spec["name"], description=goal_spec["description"])
            session.add(goal)
            await session.flush()
        else:
            goal.description = goal_spec["description"]
        goals[goal.name] = goal

        for topic_name in selected_topics:
            topic = topic_rows[topic_name]
            existing_link = (
                await session.execute(select(GoalTopic).where(GoalTopic.goal_id == goal.id, GoalTopic.topic_id == topic.id))
            ).scalar_one_or_none()
            if existing_link is None:
                session.add(GoalTopic(goal_id=goal.id, topic_id=topic.id))
    await session.flush()
    return goals


async def _seed_prerequisites(session, *, topic_rows: dict[str, Topic]) -> None:
    topic_names = list(topic_rows.keys())
    for index in range(1, len(topic_names)):
        topic = topic_rows[topic_names[index]]
        prerequisite = topic_rows[topic_names[index - 1]]
        exists = (
            await session.execute(
                select(TopicPrerequisite).where(
                    TopicPrerequisite.topic_id == topic.id,
                    TopicPrerequisite.prerequisite_topic_id == prerequisite.id,
                )
            )
        ).scalar_one_or_none()
        if exists is None:
            session.add(TopicPrerequisite(topic_id=topic.id, prerequisite_topic_id=prerequisite.id))
    await session.flush()


async def _upsert_topic_score(
    session,
    *,
    tenant_id: int,
    user_id: int,
    topic_id: int,
    diagnostic_test_id: int,
    score: float,
    mastery_delta: float,
    confidence: float,
    retention_score: float,
    review_interval_days: int,
    review_due_at: datetime,
    updated_at: datetime,
) -> None:
    existing = (
        await session.execute(select(TopicScore).where(TopicScore.user_id == user_id, TopicScore.topic_id == topic_id))
    ).scalar_one_or_none()
    if existing is None:
        session.add(
            TopicScore(
                tenant_id=tenant_id,
                user_id=user_id,
                topic_id=topic_id,
                diagnostic_test_id=diagnostic_test_id,
                score=score,
                mastery_delta=mastery_delta,
                confidence=confidence,
                retention_score=retention_score,
                review_interval_days=review_interval_days,
                review_due_at=review_due_at,
                updated_at=updated_at,
            )
        )
        return

    existing.diagnostic_test_id = diagnostic_test_id
    existing.score = score
    existing.mastery_delta = mastery_delta
    existing.confidence = confidence
    existing.retention_score = retention_score
    existing.review_interval_days = review_interval_days
    existing.review_due_at = review_due_at
    existing.updated_at = updated_at


async def _ensure_community(session, *, tenant: Tenant, topic_rows: dict[str, Topic], community_spec: dict) -> Community:
    community = (
        await session.execute(
            select(Community).where(Community.tenant_id == tenant.id, Community.name == community_spec["name"])
        )
    ).scalar_one_or_none()
    if community is None:
        community = Community(
            tenant_id=tenant.id,
            topic_id=topic_rows[community_spec["topic_name"]].id,
            name=community_spec["name"],
            description=community_spec["description"],
            created_at=_utcnow() - timedelta(days=25),
        )
        session.add(community)
        await session.flush()
    return community


def _daily_timestamp(*, rng: Random, days_ago: int, min_hour: int = 7, max_hour: int = 22) -> datetime:
    base = _utcnow() - timedelta(days=days_ago)
    hour = rng.randint(min_hour, max_hour)
    minute = rng.randint(0, 59)
    return base.replace(hour=hour, minute=minute, second=rng.randint(0, 50), microsecond=0)


async def _seed_student_activity(
    session,
    *,
    tenant: Tenant,
    student_spec: dict,
    student_index: int,
    topic_rows: dict[str, Topic],
    goal_rows: dict[str, Goal],
    communities: list[Community],
    teacher_user: User,
    mentor_user: User,
) -> User:
    rng = Random(f"{tenant.name}-{student_spec['email']}")
    user = await _ensure_user(
        session,
        tenant=tenant,
        email=student_spec["email"],
        password=student_spec["password"],
        role=UserRole.student,
        display_name=student_spec["display_name"],
    )
    user.experience_points = 700 + student_index * 190 + rng.randint(0, 180)
    user.current_streak_days = 2 + rng.randint(0, 10)
    user.focus_score = round(62 + student_index * 5 + rng.uniform(0, 14), 1)

    selected_goal = list(goal_rows.values())[student_index % len(goal_rows)]
    goal_topic_links = (
        await session.execute(select(GoalTopic).where(GoalTopic.goal_id == selected_goal.id))
    ).scalars().all()
    goal_topics = [topic_rows[next(name for name, row in topic_rows.items() if row.id == link.topic_id)] for link in goal_topic_links]
    if not goal_topics:
        goal_topics = list(topic_rows.values())[:7]

    diagnostic_started = _utcnow() - timedelta(days=28 - student_index * 2)
    diagnostic_completed = diagnostic_started + timedelta(minutes=45 + rng.randint(0, 18))
    diagnostic = (
        await session.execute(select(DiagnosticTest).where(DiagnosticTest.user_id == user.id, DiagnosticTest.goal_id == selected_goal.id))
    ).scalar_one_or_none()
    if diagnostic is None:
        diagnostic = DiagnosticTest(
            user_id=user.id,
            goal_id=selected_goal.id,
            started_at=diagnostic_started,
            completed_at=diagnostic_completed,
        )
        session.add(diagnostic)
        await session.flush()
    else:
        diagnostic.started_at = diagnostic_started
        diagnostic.completed_at = diagnostic_completed

    roadmap = (
        await session.execute(select(Roadmap).where(Roadmap.user_id == user.id, Roadmap.goal_id == selected_goal.id))
    ).scalar_one_or_none()
    if roadmap is None:
        roadmap = Roadmap(user_id=user.id, goal_id=selected_goal.id, generated_at=diagnostic_completed + timedelta(hours=3))
        session.add(roadmap)
        await session.flush()
    else:
        roadmap.generated_at = diagnostic_completed + timedelta(hours=3)

    all_questions = (
        await session.execute(select(Question).join(Topic).where(Topic.tenant_id == tenant.id))
    ).scalars().all()
    questions_by_topic_id: dict[int, list[Question]] = defaultdict(list)
    for question in all_questions:
        questions_by_topic_id[question.topic_id].append(question)

    for position, topic in enumerate(goal_topics, start=1):
        base_score = max(38.0, min(92.0, 48 + position * 4 + student_index * 3 + rng.uniform(-9, 12)))
        if position <= 2:
            progress_status = "completed"
        elif position <= 4:
            progress_status = "in_progress"
        else:
            progress_status = "pending"
        estimated = round(2.0 + rng.uniform(1.0, 4.5), 1)
        deadline = roadmap.generated_at + timedelta(days=position * 3)

        step = (
            await session.execute(
                select(RoadmapStep).where(RoadmapStep.roadmap_id == roadmap.id, RoadmapStep.topic_id == topic.id, RoadmapStep.is_revision.is_(False))
            )
        ).scalar_one_or_none()
        if step is None:
            step = RoadmapStep(
                roadmap_id=roadmap.id,
                topic_id=topic.id,
                estimated_time_hours=estimated,
                difficulty="easy" if base_score > 75 else "medium" if base_score > 58 else "hard",
                priority=position,
                deadline=deadline,
                progress_status=progress_status,
                step_type="core",
                rationale=f"Sequenced for {selected_goal.name} based on diagnostic strengths and gaps.",
                is_revision=False,
            )
            session.add(step)
        else:
            step.priority = position
            step.deadline = deadline
            step.progress_status = progress_status
            step.estimated_time_hours = estimated
            step.difficulty = "easy" if base_score > 75 else "medium" if base_score > 58 else "hard"
            step.rationale = f"Sequenced for {selected_goal.name} based on diagnostic strengths and gaps."

        if position in {2, 5}:
            revision = (
                await session.execute(
                    select(RoadmapStep).where(RoadmapStep.roadmap_id == roadmap.id, RoadmapStep.topic_id == topic.id, RoadmapStep.is_revision.is_(True))
                )
            ).scalar_one_or_none()
            if revision is None:
                session.add(
                    RoadmapStep(
                        roadmap_id=roadmap.id,
                        topic_id=topic.id,
                        estimated_time_hours=1.5,
                        difficulty="medium",
                        priority=position + 10,
                        deadline=deadline + timedelta(days=8),
                        progress_status="pending" if progress_status == "completed" else "in_progress",
                        step_type="revision",
                        rationale="Scheduled spaced repetition based on retention and recent activity.",
                        is_revision=True,
                    )
                )

        mastery_delta = round(rng.uniform(3.5, 14.0), 1)
        confidence = round(min(0.95, max(0.55, 0.58 + position * 0.03 + rng.uniform(-0.08, 0.12))), 2)
        retention_score = round(max(42.0, min(94.0, base_score - rng.uniform(4.0, 16.0))), 1)
        review_interval = rng.choice([3, 5, 7, 10])
        review_due_at = _utcnow() + timedelta(days=rng.randint(-2, 8))
        await _upsert_topic_score(
            session,
            tenant_id=tenant.id,
            user_id=user.id,
            topic_id=topic.id,
            diagnostic_test_id=diagnostic.id,
            score=round(base_score, 1),
            mastery_delta=mastery_delta,
            confidence=confidence,
            retention_score=retention_score,
            review_interval_days=review_interval,
            review_due_at=review_due_at,
            updated_at=_utcnow() - timedelta(days=rng.randint(0, 3)),
        )

        for question in questions_by_topic_id[topic.id][:2]:
            answer = (
                await session.execute(select(UserAnswer).where(UserAnswer.test_id == diagnostic.id, UserAnswer.question_id == question.id))
            ).scalar_one_or_none()
            is_correct = base_score >= 67 or (base_score >= 56 and question.difficulty <= 2)
            response_value = question.correct_answer if is_correct else question.answer_options[-1]
            if answer is None:
                session.add(
                    UserAnswer(
                        test_id=diagnostic.id,
                        question_id=question.id,
                        user_answer=response_value,
                        score=round(base_score if is_correct else max(18.0, base_score - 26.0), 1),
                        time_taken=round(28 + rng.uniform(10.0, 65.0), 1),
                    )
                )
            else:
                answer.user_answer = response_value
                answer.score = round(base_score if is_correct else max(18.0, base_score - 26.0), 1)
                answer.time_taken = round(28 + rng.uniform(10.0, 65.0), 1)

        suggestion = (
            await session.execute(
                select(MentorSuggestion).where(MentorSuggestion.user_id == user.id, MentorSuggestion.topic_id == topic.id)
            )
        ).scalar_one_or_none()
        if suggestion is None and position <= 3:
            session.add(
                MentorSuggestion(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    topic_id=topic.id,
                    suggestion_type="focus",
                    title=f"Focus on {topic.name} next",
                    message=f"Spend your next focused block on {topic.name} and finish one concrete artifact.",
                    why_reason=f"{topic.name} is materially affecting progress toward {selected_goal.name}.",
                    is_ai_generated=position % 2 == 0,
                    created_at=_utcnow() - timedelta(days=rng.randint(0, 5)),
                )
            )

    await session.flush()

    for community in communities:
        membership = (
            await session.execute(
                select(CommunityMember).where(CommunityMember.community_id == community.id, CommunityMember.user_id == user.id)
            )
        ).scalar_one_or_none()
        if membership is None:
            session.add(
                CommunityMember(
                    tenant_id=tenant.id,
                    community_id=community.id,
                    user_id=user.id,
                    role="student",
                    joined_at=_utcnow() - timedelta(days=rng.randint(5, 24)),
                )
            )

    for days_ago in range(29, -1, -1):
        event_count = 1 if rng.random() > 0.28 else 0
        if days_ago in {0, 1, 2, 6, 13, 20}:
            event_count += 1
        for _ in range(event_count):
            event_type = rng.choice(LEARNING_EVENT_TYPES)
            topic = goal_topics[rng.randrange(len(goal_topics))]
            created_at = _daily_timestamp(rng=rng, days_ago=days_ago)
            existing = (
                await session.execute(
                    select(LearningEvent).where(
                        LearningEvent.user_id == user.id,
                        LearningEvent.event_type == event_type,
                        LearningEvent.created_at == created_at,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    LearningEvent(
                        tenant_id=tenant.id,
                        user_id=user.id,
                        event_type=event_type,
                        topic_id=topic.id if event_type != "mentor_checkin" else None,
                        diagnostic_test_id=diagnostic.id if event_type in {"practice_quiz", "mentor_checkin"} else None,
                        metadata_json=json.dumps(
                            {
                                "minutes": 12 + rng.randint(8, 55),
                                "source": "demo_seed",
                                "device": rng.choice(["web", "mobile_web"]),
                                "completion_delta": rng.randint(1, 12),
                            }
                        ),
                        created_at=created_at,
                    )
                )

    chosen_badges = BADGE_LIBRARY[: 2 + (student_index % 2)]
    for badge_name, description, awarded_for in chosen_badges:
        existing_badge = (
            await session.execute(select(Badge).where(Badge.user_id == user.id, Badge.name == badge_name))
        ).scalar_one_or_none()
        if existing_badge is None:
            session.add(
                Badge(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    name=badge_name,
                    description=description,
                    awarded_for=awarded_for,
                    awarded_at=_utcnow() - timedelta(days=rng.randint(0, 18)),
                )
            )

    return user


async def _seed_community_activity(
    session,
    *,
    tenant: Tenant,
    communities: list[Community],
    users: list[User],
    topic_rows: dict[str, Topic],
) -> None:
    rng = Random(f"community-{tenant.name}")
    students = [user for user in users if user.role == UserRole.student]
    staff = [user for user in users if user.role in {UserRole.teacher, UserRole.mentor, UserRole.admin}]
    for community in communities:
        topic = next(topic for topic in topic_rows.values() if topic.id == community.topic_id)
        for index in range(3):
            author = students[index % len(students)]
            title = f"{topic.name}: demo thread {index + 1}"
            thread = (
                await session.execute(
                    select(DiscussionThread).where(DiscussionThread.tenant_id == tenant.id, DiscussionThread.community_id == community.id, DiscussionThread.title == title)
                )
            ).scalar_one_or_none()
            if thread is None:
                thread = DiscussionThread(
                    tenant_id=tenant.id,
                    community_id=community.id,
                    author_user_id=author.id,
                    title=title,
                    body=f"I am working through {topic.name} and want a practical rule of thumb plus one example I can reuse.",
                    is_resolved=index != 1,
                    upvotes=18 + rng.randint(0, 55),
                    ai_summary=f"Believable seeded summary for {topic.name}: focus on one principle, one artifact, and one common mistake.",
                    is_ai_assisted=index % 2 == 0,
                    created_at=_utcnow() - timedelta(days=18 - index * 3),
                )
                session.add(thread)
                await session.flush()
            for reply_index in range(2):
                reply_author = (staff + students)[(index + reply_index) % (len(staff) + len(students))]
                body = (
                    f"Start with the artifact for {topic.name}, then check the most common pitfall before you submit."
                    if reply_index == 0
                    else f"I used a short checklist and one worked example to get more consistent on {topic.name}."
                )
                reply = (
                    await session.execute(
                        select(DiscussionReply).where(DiscussionReply.thread_id == thread.id, DiscussionReply.author_user_id == reply_author.id, DiscussionReply.body == body)
                    )
                ).scalar_one_or_none()
                if reply is None:
                    reply = DiscussionReply(
                        tenant_id=tenant.id,
                        thread_id=thread.id,
                        author_user_id=reply_author.id,
                        body=body,
                        upvotes=9 + rng.randint(0, 34),
                        is_best_answer=reply_index == 0 and thread.is_resolved,
                        is_ai_assisted=reply_index == 1,
                        created_at=thread.created_at + timedelta(hours=reply_index + 2),
                    )
                    session.add(reply)
                    await session.flush()
                if reply.is_best_answer:
                    thread.best_answer_reply_id = reply.id


async def _seed_experiments(session, *, tenant: Tenant) -> None:
    experiment = (
        await session.execute(select(Experiment).where(Experiment.tenant_id == tenant.id, Experiment.key == "premium_dashboard_rollout"))
    ).scalar_one_or_none()
    if experiment is None:
        experiment = Experiment(
            tenant_id=tenant.id,
            key="premium_dashboard_rollout",
            name="Premium Dashboard Rollout",
            description="Compare a calmer productivity layout against an intelligence-rich layout for weekly engagement.",
            status="running",
            success_metric="weekly_active_minutes",
            created_at=_utcnow() - timedelta(days=21),
        )
        session.add(experiment)
        await session.flush()
        session.add_all(
            [
                ExperimentVariant(
                    experiment_id=experiment.id,
                    name="calm_focus",
                    config_json='{"layout":"focus-first","motion":"moderate"}',
                    population_size=512,
                    conversion_rate=24.8,
                    engagement_lift=0.0,
                    created_at=_utcnow() - timedelta(days=21),
                ),
                ExperimentVariant(
                    experiment_id=experiment.id,
                    name="intelligence_plus",
                    config_json='{"layout":"intelligence-rich","motion":"expressive"}',
                    population_size=538,
                    conversion_rate=31.2,
                    engagement_lift=14.9,
                    created_at=_utcnow() - timedelta(days=21),
                ),
            ]
        )


async def seed() -> None:
    seeded_tenants: list[tuple[Tenant, list[dict]]] = []
    async with AsyncSessionLocal() as session:
        platform_tenant, super_admin = await _seed_platform_super_admin(session)
        tenant_specs = build_demo_tenants()
        for tenant_spec in tenant_specs:
            tenant = await _get_or_create_tenant(session, name=tenant_spec["name"], tenant_type=tenant_spec["type"])

            staff_users: list[User] = []
            for user_spec in tenant_spec["panel_users"]:
                staff_users.append(
                    await _ensure_user(
                        session,
                        tenant=tenant,
                        email=user_spec["email"],
                        password=user_spec["password"],
                        role=user_spec["role"],
                        display_name=user_spec["label"].replace(" Panel", ""),
                    )
                )

            topic_rows = await _seed_topics(session, tenant=tenant, topic_specs=tenant_spec["topics"])
            goal_rows = await _seed_goals(session, tenant=tenant, goal_specs=tenant_spec["goals"], topic_rows=topic_rows)
            await _seed_prerequisites(session, topic_rows=topic_rows)
            communities = [
                await _ensure_community(session, tenant=tenant, topic_rows=topic_rows, community_spec=community_spec)
                for community_spec in tenant_spec["communities"]
            ]

            teacher_user = next(user for user in staff_users if user.role == UserRole.teacher)
            mentor_user = next(user for user in staff_users if user.role == UserRole.mentor)
            student_users: list[User] = []
            for student_index, student_spec in enumerate(tenant_spec["students"]):
                student_users.append(
                    await _seed_student_activity(
                        session,
                        tenant=tenant,
                        student_spec=student_spec,
                        student_index=student_index,
                        topic_rows=topic_rows,
                        goal_rows=goal_rows,
                        communities=communities,
                        teacher_user=teacher_user,
                        mentor_user=mentor_user,
                    )
                )

            await _seed_community_activity(
                session,
                tenant=tenant,
                communities=communities,
                users=[*staff_users, *student_users],
                topic_rows=topic_rows,
            )
            await _seed_experiments(session, tenant=tenant)
            seeded_tenants.append((tenant, [*tenant_spec["panel_users"], *tenant_spec["students"]]))

        await session.commit()

    print("PLATFORM ACCESS")
    print(f"tenant: {platform_tenant.name}")
    print(f"tenant_id: {platform_tenant.id}")
    print(f"{super_admin['label']}: {super_admin['email']} / {super_admin['password']}")
    print()
    print("PANEL TEST CREDENTIALS")
    for tenant, user_specs in seeded_tenants:
        print(f"tenant: {tenant.name}")
        print(f"tenant_id: {tenant.id}")
        for user_spec in user_specs:
            label = user_spec.get("label") or user_spec.get("display_name") or "Student"
            print(f"- {label}: {user_spec['email']} / {user_spec['password']}")
        print()


if __name__ == "__main__":
    asyncio.run(seed())
