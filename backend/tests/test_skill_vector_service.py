import asyncio
from datetime import datetime, timezone

from app.application.services.skill_vector_service import SkillVectorService


class _VectorRow:
    def __init__(self, tenant_id: int, user_id: int, topic_id: int, mastery_score: float, confidence_score: float, last_updated):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.topic_id = topic_id
        self.mastery_score = mastery_score
        self.confidence_score = confidence_score
        self.last_updated = last_updated


class _Repo:
    def __init__(self):
        self.rows: dict[tuple[int, int, int], _VectorRow] = {}

    async def get_for_user_topic(self, *, tenant_id: int, user_id: int, topic_id: int):
        return self.rows.get((tenant_id, user_id, topic_id))

    async def upsert(self, *, tenant_id: int, user_id: int, topic_id: int, mastery_score: float, confidence_score: float, last_updated):
        row = self.rows.get((tenant_id, user_id, topic_id))
        if row is None:
            row = _VectorRow(tenant_id, user_id, topic_id, mastery_score, confidence_score, last_updated)
            self.rows[(tenant_id, user_id, topic_id)] = row
        else:
            row.mastery_score = mastery_score
            row.confidence_score = confidence_score
            row.last_updated = last_updated
        return row

    async def list_for_user(self, *, tenant_id: int, user_id: int):
        return [row for row in self.rows.values() if row.tenant_id == tenant_id and row.user_id == user_id]


class _Session:
    async def execute(self, _stmt):
        raise AssertionError("This unit test should not execute SQL")

    async def commit(self):
        return None


def test_skill_vector_updates_from_diagnostic_and_progress():
    async def _run():
        service = SkillVectorService(_Session())
        service.repository = _Repo()

        first = await service.update_from_diagnostic_answer(
            tenant_id=1,
            user_id=2,
            topic_id=3,
            score=80.0,
            time_taken_seconds=20.0,
            answered_at=datetime.now(timezone.utc),
        )
        assert first["mastery_score"] > 0
        assert first["confidence_score"] > 0

        second = await service.update_from_progress(
            tenant_id=1,
            user_id=2,
            topic_id=3,
            progress_status="completed",
            observed_at=datetime.now(timezone.utc),
        )
        assert second["mastery_score"] >= first["mastery_score"]
        assert second["confidence_score"] >= first["confidence_score"]

    asyncio.run(_run())
