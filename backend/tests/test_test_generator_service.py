import asyncio
from types import SimpleNamespace

from app.application.services.test_generator_service import SmartTestGeneratorService


class _TopicScoreRepository:
    async def list_by_user(self, *, tenant_id: int, user_id: int):
        _ = tenant_id, user_id
        return [
            SimpleNamespace(topic_id=11, score=32.0, confidence=0.35),
            SimpleNamespace(topic_id=12, score=58.0, confidence=0.65),
            SimpleNamespace(topic_id=13, score=84.0, confidence=0.82),
        ]


class _DiagnosticRepository:
    def __init__(self):
        self.created_test = None
        self.created_state = None

    async def latest_goal_id_for_user(self, *, user_id: int, tenant_id: int):
        _ = user_id, tenant_id
        return 9

    async def answered_question_ids_for_user(self, *, user_id: int, tenant_id: int):
        _ = user_id, tenant_id
        return [101, 202]

    async def create_test(self, user_id: int, goal_id: int, started_at):
        self.created_test = {"user_id": user_id, "goal_id": goal_id, "started_at": started_at}
        return SimpleNamespace(id=55, user_id=user_id, goal_id=goal_id, started_at=started_at, completed_at=None)

    async def upsert_test_state(self, **kwargs):
        self.created_state = kwargs
        return SimpleNamespace(test_id=kwargs["test_id"], planned_question_ids=kwargs["planned_question_ids"])


class _GoalRepository:
    async def get_by_id(self, *, tenant_id: int, goal_id: int):
        _ = tenant_id
        return SimpleNamespace(id=goal_id)


class _TopicRepository:
    async def list_topics_by_ids(self, topic_ids: list[int], tenant_id: int):
        _ = tenant_id
        names = {
            11: "SQL Basics",
            12: "Joins",
            13: "Indexes",
        }
        return [SimpleNamespace(id=topic_id, name=names[topic_id]) for topic_id in topic_ids]

    async def list_questions_for_topics(self, *, tenant_id: int, topic_ids: list[int], exclude_question_ids=None, goal_id=None):
        _ = tenant_id, goal_id
        excluded = set(exclude_question_ids or [])
        rows = [
            SimpleNamespace(id=101, topic_id=11, difficulty=1, question_type="multiple_choice", question_text="repeat", answer_options=["a"]),
            SimpleNamespace(id=102, topic_id=11, difficulty=1, question_type="multiple_choice", question_text="easy weak", answer_options=["a"]),
            SimpleNamespace(id=103, topic_id=11, difficulty=2, question_type="multiple_choice", question_text="medium weak", answer_options=["a"]),
            SimpleNamespace(id=201, topic_id=12, difficulty=2, question_type="multiple_choice", question_text="medium weak 2", answer_options=["a"]),
            SimpleNamespace(id=203, topic_id=12, difficulty=3, question_type="multiple_choice", question_text="hard weak 2", answer_options=["a"]),
            SimpleNamespace(id=301, topic_id=13, difficulty=3, question_type="multiple_choice", question_text="hard strong", answer_options=["a"]),
        ]
        return [row for row in rows if row.topic_id in topic_ids and row.id not in excluded]


def test_generate_smart_test_prioritizes_weak_topics_and_mixes_difficulty():
    async def _run():
        class _Session:
            async def commit(self):
                return None

        diagnostic_repository = _DiagnosticRepository()
        service = SmartTestGeneratorService(session=_Session())
        service.topic_score_repository = _TopicScoreRepository()
        service.diagnostic_repository = diagnostic_repository
        service.topic_repository = _TopicRepository()
        service.goal_repository = _GoalRepository()

        result = await service.generate_smart_test(
            tenant_id=3,
            user_id=7,
            goal_id=9,
            question_count=4,
        )

        assert result["test_id"] == 55
        assert result["persisted_session"] is True
        assert result["next_question_id"] == result["questions"][0]["id"]
        assert result["question_count"] == 4
        assert result["repeated_question_count"] == 0
        assert all(question["id"] != 101 for question in result["questions"])
        assert result["generated_from_weak_topics"][0]["topic_id"] == 11
        assert result["generated_from_weak_topics"][0]["target_difficulty"] == 1
        assert result["difficulty_mix"]["easy"] >= 1
        assert result["difficulty_mix"]["medium"] >= 1
        assert diagnostic_repository.created_state["planned_question_ids"][0] == result["next_question_id"]

    asyncio.run(_run())
