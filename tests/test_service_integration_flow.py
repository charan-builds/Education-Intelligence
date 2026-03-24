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
    generated_at: datetime
    steps: list = field(default_factory=list)


class _Session:
    async def execute(self, _stmt):
        class _Result:
            @staticmethod
            def scalar_one_or_none():
                return None

        return _Result()

    async def commit(self):
        return None

    async def rollback(self):
        return None


class _TenantRepo:
    async def get_by_id(self, tenant_id: int):
        if tenant_id == 1:
            return _Tenant(id=1, name="Platform", type=TenantType.platform)
        return None


class _UserRepo:
    def __init__(self):
        self.users = {}
        self.next_id = 1

    async def get_by_email(self, email: str):
        return self.users.get(email)

    async def create(self, tenant_id, email, password_hash, role, created_at):
        user = _User(
            id=self.next_id,
            tenant_id=tenant_id,
            email=email,
            password_hash=password_hash,
            role=role,
        )
        self.next_id += 1
        self.users[email] = user
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

    async def get_test_for_user(self, test_id, user_id, tenant_id):
        test = self.tests.get(test_id)
        if test and test.user_id == user_id and tenant_id == 1:
            return test
        return None

    async def add_answer(self, test_id, question_id, user_answer, score, time_taken):
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


class _RoadmapRepo:
    def __init__(self):
        self.roadmaps = []
        self.next_id = 1
        self.next_step_id = 1

    async def create_roadmap(self, user_id, goal_id, generated_at):
        roadmap = _Roadmap(id=self.next_id, user_id=user_id, goal_id=goal_id, generated_at=generated_at)
        self.next_id += 1
        self.roadmaps.append(roadmap)
        return roadmap

    async def add_step(
        self,
        roadmap_id,
        topic_id,
        deadline,
        estimated_time_hours=4.0,
        difficulty="medium",
        priority=1,
        progress_status="pending",
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
            tenant_id=1,
            email="student@platform.local",
            password="secret123",
            role=UserRole.student,
        )
        token, logged = await auth.login(email="student@platform.local", password="secret123")

        assert user.id == logged.id
        assert isinstance(token, str)
        assert token

        diagnostic_repo = _DiagnosticRepo()
        topic_repo = _TopicRepo()

        diagnostic = DiagnosticService(session)
        diagnostic.diagnostic_repository = diagnostic_repo
        diagnostic.topic_repository = topic_repo

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

        scores = await diagnostic.get_result(test.id, user.id, 1)
        assert 101 in scores and 102 in scores

        roadmap_repo = _RoadmapRepo()
        roadmap = RoadmapService(session)
        roadmap.diagnostic_repository = diagnostic_repo
        roadmap.topic_repository = topic_repo
        roadmap.roadmap_repository = roadmap_repo

        created = await roadmap.generate(user_id=user.id, tenant_id=1, goal_id=1, test_id=test.id)
        assert created.user_id == user.id
        assert len(created.steps) >= 1

        own_roadmaps = await roadmap.list_for_user(user.id, 1, limit=20, offset=0)
        foreign_roadmaps = await roadmap.list_for_user(user.id, 999, limit=20, offset=0)
        assert len(own_roadmaps) == 1
        assert foreign_roadmaps == []

    asyncio.run(_run())
