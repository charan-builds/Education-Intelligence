import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.application.services.auth_service import AuthService
from app.application.services.diagnostic_service import DiagnosticService
from app.application.services.roadmap_service import RoadmapService
from app.domain.models.tenant import TenantType
from app.domain.models.user import UserRole


@dataclass
class _Tenant:
    id: int
    name: str
    type: TenantType
    subdomain: str | None = None


@dataclass
class _User:
    id: int
    tenant_id: int
    email: str
    password_hash: str
    role: UserRole


@dataclass
class _Question:
    id: int
    topic_id: int
    correct_answer: str
    difficulty: int = 2
    accepted_answers: list[str] | None = None


@dataclass
class _Test:
    id: int
    user_id: int
    goal_id: int
    started_at: datetime
    completed_at: datetime | None = None


@dataclass
class _Roadmap:
    id: int
    user_id: int
    goal_id: int
    test_id: int
    status: str
    error_message: str | None
    generated_at: datetime
    steps: list = field(default_factory=list)


class _Session:
    def add(self, _obj):
        return None

    async def flush(self):
        return None

    async def delete(self, _obj):
        return None

    async def execute(self, _stmt):
        class _Result:
            @staticmethod
            def scalar_one_or_none():
                return None

            @staticmethod
            def scalar_one():
                return 0

        return _Result()

    async def scalar(self, _stmt):
        return None

    async def commit(self):
        return None

    async def rollback(self):
        return None


class _TenantRepo:
    async def get_by_id(self, tenant_id: int):
        if tenant_id == 1:
            return _Tenant(id=1, name="Platform", type=TenantType.platform, subdomain="platform")
        return None

    async def get_by_subdomain(self, subdomain: str):
        if subdomain == "platform":
            return _Tenant(id=1, name="Platform", type=TenantType.platform, subdomain="platform")
        return None


class _UserRepo:
    def __init__(self):
        self.users = {}
        self.next_id = 1

    async def get_by_email(self, email: str, *, tenant_id: int | None = None):
        user = self.users.get((tenant_id, email)) if tenant_id is not None else None
        if user is not None:
            return user
        if tenant_id is None:
            for (stored_tenant_id, stored_email), stored_user in self.users.items():
                if stored_email == email:
                    return stored_user
        return None

    async def create(self, tenant_id, email, password_hash, role, created_at):
        user = _User(
            id=self.next_id,
            tenant_id=tenant_id,
            email=email,
            password_hash=password_hash,
            role=role,
        )
        self.next_id += 1
        self.users[(tenant_id, email)] = user
        return user


class _TopicRepo:
    async def get_question(self, question_id: int):
        return _Question(
            id=question_id,
            topic_id=101 if question_id == 1 else 102,
            correct_answer="ans1" if question_id == 1 else "ans2",
            accepted_answers=["answer one"] if question_id == 1 else ["answer two"],
        )

    async def get_prerequisite_edges(self, tenant_id=None):
        return [(102, 101)]

    async def list_questions_by_ids(self, *, tenant_id: int, question_ids: list[int]):
        if tenant_id != 1:
            return []
        return [await self.get_question(question_id) for question_id in question_ids]


class _GoalRepo:
    async def get_by_id(self, *, tenant_id: int, goal_id: int):
        if tenant_id == 1 and goal_id == 1:
            return type("_Goal", (), {"id": 1})()
        return None


class _LearningEventService:
    async def track_question_answered(self, **kwargs):
        return None

    async def track_diagnostic_completed(self, **kwargs):
        return None


class _SkillVectorService:
    async def update_from_diagnostic_answer(self, **kwargs):
        return None


class _RetentionService:
    async def upsert_topic_score(self, **kwargs):
        return None


class _MlPlatformService:
    async def build_feature_snapshot(self, **kwargs):
        return None


class _FeatureFlagService:
    async def is_enabled(self, *args, **kwargs):
        return False


class _CacheService:
    async def bump_namespace_version(self, *args, **kwargs):
        return None


class _DiagnosticRepo:
    def __init__(self):
        self.tests = {}
        self.answers = []
        self.next_test_id = 1

    async def create_test(self, user_id, goal_id, started_at):
        test = _Test(id=self.next_test_id, user_id=user_id, goal_id=goal_id, started_at=started_at)
        self.tests[test.id] = test
        self.next_test_id += 1
        return test

    async def get_test_for_user(self, test_id, user_id, tenant_id, for_update=False):
        test = self.tests.get(test_id)
        if test and test.user_id == user_id and tenant_id == 1:
            return test
        return None

    async def get_answer_for_test_question(self, *, test_id, question_id, for_update=False):
        for stored_test_id, stored_question_id, _score in self.answers:
            if stored_test_id == test_id and stored_question_id == question_id:
                return type("_Answer", (), {"test_id": test_id, "question_id": question_id, "attempt_count": 1})()
        return None

    async def upsert_answer(self, *, test_id, question_id, user_answer, score, time_taken, accuracy, attempt_count):
        existing_index = next(
            (
                index
                for index, (stored_test_id, stored_question_id, _score) in enumerate(self.answers)
                if stored_test_id == test_id and stored_question_id == question_id
            ),
            None,
        )
        if existing_index is None:
            self.answers.append((test_id, question_id, score))
        else:
            self.answers[existing_index] = (test_id, question_id, score)
        return type(
            "_Answer",
            (),
            {
                "test_id": test_id,
                "question_id": question_id,
                "score": score,
                "accuracy": accuracy,
                "attempt_count": attempt_count,
                "time_taken": time_taken,
            },
        )()

    async def get_latest_open_test_for_user(self, *, user_id, goal_id, tenant_id):
        if tenant_id != 1:
            return None
        open_tests = [
            test for test in self.tests.values() if test.user_id == user_id and test.goal_id == goal_id and test.completed_at is None
        ]
        return open_tests[-1] if open_tests else None

    async def add_answer(self, test_id, question_id, user_answer, score, time_taken, accuracy, attempt_count=1):
        self.answers.append((test_id, question_id, score))

    async def complete_test(self, test, completed_at):
        test.completed_at = completed_at
        return test

    async def topic_scores_for_test(self, test_id, user_id, tenant_id):
        if tenant_id != 1:
            return {}
        topic_map = {1: 101, 2: 102}
        per_topic = {}
        for t_id, q_id, score in self.answers:
            if t_id != test_id:
                continue
            topic_id = topic_map[q_id]
            per_topic.setdefault(topic_id, []).append(score)
        return {topic: sum(scores) / len(scores) for topic, scores in per_topic.items()}

    async def answer_analytics_for_test(self, test_id, user_id, tenant_id):
        by_question = {1: (5.0, 45.0, 1), 2: (7.0, 55.0, 2)}
        rows = [by_question[q_id] for t_id, q_id, _ in self.answers if t_id == test_id and q_id in by_question]
        return {
            "response_times": [r[0] for r in rows],
            "accuracies": [r[1] for r in rows],
            "difficulty_distribution": {
                "easy": sum(1 for _, _, d in rows if d == 1),
                "medium": sum(1 for _, _, d in rows if d == 2),
                "hard": sum(1 for _, _, d in rows if d >= 3),
            },
        }

    async def list_answers_for_test(self, *, test_id):
        return [
            type(
                "_Answer",
                (),
                {
                    "question_id": q_id,
                    "score": score,
                    "accuracy": round(score / 100.0, 4),
                    "attempt_count": 1,
                    "time_taken": 5.0 if q_id == 1 else 7.0,
                },
            )()
            for t_id, q_id, score in self.answers
            if t_id == test_id
        ]


class _RoadmapRepo:
    def __init__(self):
        self.roadmaps = []
        self.next_id = 1
        self.next_step_id = 1

    async def get_by_identity(self, *, user_id, goal_id, test_id, tenant_id, for_update=False):
        if tenant_id != 1:
            return None
        return next(
            (r for r in self.roadmaps if r.user_id == user_id and r.goal_id == goal_id and r.test_id == test_id),
            None,
        )

    async def create_roadmap(self, user_id, goal_id, test_id, generated_at, status="generating", error_message=None):
        roadmap = _Roadmap(
            id=self.next_id,
            user_id=user_id,
            goal_id=goal_id,
            test_id=test_id,
            status=status,
            error_message=error_message,
            generated_at=generated_at,
        )
        self.next_id += 1
        self.roadmaps.append(roadmap)
        return roadmap

    async def mark_status(self, roadmap, *, status, error_message=None):
        roadmap.status = status
        roadmap.error_message = error_message
        return roadmap

    async def clear_steps(self, roadmap):
        roadmap.steps.clear()

    async def add_step(
        self,
        roadmap_id,
        topic_id,
        deadline,
        estimated_time_hours=4.0,
        difficulty="medium",
        priority=1,
        progress_status="pending",
        step_type="core",
        rationale=None,
    ):
        roadmap = next(r for r in self.roadmaps if r.id == roadmap_id)
        roadmap.steps.append(
            {
                "id": self.next_step_id,
                "topic_id": topic_id,
                "estimated_time_hours": estimated_time_hours,
                "difficulty": difficulty,
                "priority": priority,
                "deadline": deadline,
                "progress_status": progress_status,
            }
        )
        self.next_step_id += 1

    async def get_roadmap_for_user(self, *, roadmap_id, user_id, tenant_id):
        if tenant_id != 1:
            return None
        return next((r for r in self.roadmaps if r.id == roadmap_id and r.user_id == user_id), None)

    async def list_user_roadmaps(self, user_id, tenant_id, limit, offset):
        if tenant_id != 1:
            return []
        filtered = [r for r in self.roadmaps if r.user_id == user_id]
        return filtered[offset : offset + limit]


def test_end_to_end_service_flow_with_tenant_scope():
    async def _run():
        session = _Session()

        user_repo = _UserRepo()
        tenant_repo = _TenantRepo()

        auth = AuthService(session)
        auth.user_repository = user_repo
        auth.tenant_repository = tenant_repo

        user = await auth.register(
            email="student@platform.local",
            password="secret123",
        )
        token, refresh_token, logged, role = await auth.login(
            email="student@platform.local",
            password="secret123",
            tenant_id=1,
        )

        assert user.id == logged.id
        assert role == UserRole.student
        assert isinstance(token, str)
        assert token
        assert isinstance(refresh_token, str)
        assert refresh_token

        diagnostic_repo = _DiagnosticRepo()
        topic_repo = _TopicRepo()

        diagnostic = DiagnosticService(session)
        diagnostic.diagnostic_repository = diagnostic_repo
        diagnostic.topic_repository = topic_repo
        diagnostic.goal_repository = _GoalRepo()
        diagnostic.learning_event_service = _LearningEventService()
        diagnostic.skill_vector_service = _SkillVectorService()
        diagnostic.retention_service = _RetentionService()
        diagnostic.ml_platform_service = _MlPlatformService()

        test = await diagnostic.start_test(user_id=user.id, goal_id=1)
        await diagnostic.submit_answers(
            test_id=test.id,
            user_id=user.id,
            tenant_id=1,
            answers=[
                {"question_id": 1, "user_answer": "ans1", "time_taken": 5.0},
                {"question_id": 2, "user_answer": "ans2", "time_taken": 7.0},
            ],
        )

        result = await diagnostic.get_result(test.id, user.id, 1)
        scores = result["topic_scores"]
        assert 101 in scores and 102 in scores

        roadmap_repo = _RoadmapRepo()
        roadmap = RoadmapService(session)
        roadmap.diagnostic_repository = diagnostic_repo
        roadmap.topic_repository = topic_repo
        roadmap.roadmap_repository = roadmap_repo
        roadmap.feature_flag_service = _FeatureFlagService()
        roadmap.cache_service = _CacheService()

        created = await roadmap.generate(user_id=user.id, tenant_id=1, goal_id=1, test_id=test.id)
        assert created.user_id == user.id
        assert created.test_id == test.id
        assert created.status == "ready"
        assert len(created.steps) >= 1

        own_roadmaps = await roadmap.list_for_user(user.id, 1, limit=20, offset=0)
        foreign_roadmaps = await roadmap.list_for_user(user.id, 999, limit=20, offset=0)
        assert len(own_roadmaps) == 1
        assert foreign_roadmaps == []

        duplicate, should_enqueue = await roadmap.ensure_generation_requested(user.id, 1, goal_id=1, test_id=test.id)
        assert duplicate.id == created.id
        assert should_enqueue is False

    asyncio.run(_run())
