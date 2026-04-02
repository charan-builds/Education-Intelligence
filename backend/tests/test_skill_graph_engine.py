import asyncio

from app.domain.engines.skill_graph_engine import SkillGraphEngine, UserSkillLevel


class _Session:
    pass


def test_get_user_skill_levels_level_mapping():
    class _Engine(SkillGraphEngine):
        async def get_user_skill_levels(self, user_id: int):
            return [
                UserSkillLevel(skill_id=1, skill_name="Data Analysis", average_score=42.0, level=self._level_from_score(42.0)),
                UserSkillLevel(skill_id=2, skill_name="ML Modeling", average_score=66.0, level=self._level_from_score(66.0)),
                UserSkillLevel(skill_id=3, skill_name="Deployment", average_score=88.0, level=self._level_from_score(88.0)),
            ]

    async def _run():
        engine = _Engine(_Session(), tenant_id=10)
        levels = await engine.get_user_skill_levels(user_id=7)
        assert [item.level for item in levels] == ["beginner", "needs_practice", "mastered"]

    asyncio.run(_run())


def test_compute_skill_progress_summary_and_overall_progress():
    class _Engine(SkillGraphEngine):
        async def get_user_skill_levels(self, user_id: int):
            return [
                UserSkillLevel(skill_id=1, skill_name="Data Analysis", average_score=40.0, level="beginner"),
                UserSkillLevel(skill_id=2, skill_name="ML Modeling", average_score=70.0, level="needs_practice"),
                UserSkillLevel(skill_id=3, skill_name="Deployment", average_score=80.0, level="mastered"),
            ]

    async def _run():
        engine = _Engine(_Session(), tenant_id=2)
        progress = await engine.compute_skill_progress(user_id=99)
        assert progress["overall_progress"] == 63.33
        assert progress["summary"] == {"mastered": 1, "needs_practice": 1, "beginner": 1}
        assert progress["tenant_id"] == 2

    asyncio.run(_run())


def test_compute_skill_progress_empty_state():
    class _Engine(SkillGraphEngine):
        async def get_user_skill_levels(self, user_id: int):
            return []

    async def _run():
        engine = _Engine(_Session(), tenant_id=4)
        progress = await engine.compute_skill_progress(user_id=1)
        assert progress["overall_progress"] == 0.0
        assert progress["skills"] == []
        assert progress["summary"] == {"mastered": 0, "needs_practice": 0, "beginner": 0}

    asyncio.run(_run())
