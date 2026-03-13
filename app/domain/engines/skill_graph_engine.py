from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.diagnostic_test import DiagnosticTest
from app.domain.models.question import Question
from app.domain.models.skill import Skill
from app.domain.models.topic_skill import TopicSkill
from app.domain.models.user_answer import UserAnswer
from app.infrastructure.repositories.tenant_scoping import tenant_user_scope


@dataclass(frozen=True)
class UserSkillLevel:
    skill_id: int
    skill_name: str
    average_score: float
    level: str


class SkillGraphEngine:
    """
    Computes user skill levels from topic->skill mappings and diagnostic answers.

    Multi-tenant isolation is enforced via tenant-scoped joins.
    """

    def __init__(self, session: AsyncSession, tenant_id: int):
        self.session = session
        self.tenant_id = tenant_id

    async def get_user_skill_levels(self, user_id: int) -> list[UserSkillLevel]:
        result = await self.session.execute(
            select(
                Skill.id,
                Skill.name,
                func.avg(UserAnswer.score).label("avg_score"),
            )
            .join(TopicSkill, TopicSkill.skill_id == Skill.id)
            .join(Question, Question.topic_id == TopicSkill.topic_id)
            .join(UserAnswer, UserAnswer.question_id == Question.id)
            .join(DiagnosticTest, DiagnosticTest.id == UserAnswer.test_id)
            .where(
                Skill.tenant_id == self.tenant_id,
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, self.tenant_id),
            )
            .group_by(Skill.id, Skill.name)
            .order_by(Skill.id.asc())
        )

        rows = list(result.all())
        return [
            UserSkillLevel(
                skill_id=int(skill_id),
                skill_name=str(skill_name),
                average_score=round(float(avg_score), 2),
                level=self._level_from_score(float(avg_score)),
            )
            for skill_id, skill_name, avg_score in rows
        ]

    async def compute_skill_progress(self, user_id: int) -> dict:
        levels = await self.get_user_skill_levels(user_id)
        if not levels:
            return {
                "user_id": user_id,
                "tenant_id": self.tenant_id,
                "overall_progress": 0.0,
                "skills": [],
                "summary": {
                    "mastered": 0,
                    "needs_practice": 0,
                    "beginner": 0,
                },
            }

        mastered = sum(1 for item in levels if item.level == "mastered")
        needs_practice = sum(1 for item in levels if item.level == "needs_practice")
        beginner = sum(1 for item in levels if item.level == "beginner")
        overall_progress = round(sum(item.average_score for item in levels) / len(levels), 2)

        return {
            "user_id": user_id,
            "tenant_id": self.tenant_id,
            "overall_progress": overall_progress,
            "skills": [
                {
                    "skill_id": item.skill_id,
                    "skill_name": item.skill_name,
                    "average_score": item.average_score,
                    "level": item.level,
                }
                for item in levels
            ],
            "summary": {
                "mastered": mastered,
                "needs_practice": needs_practice,
                "beginner": beginner,
            },
        }

    @staticmethod
    def _level_from_score(score: float) -> str:
        if score < 50:
            return "beginner"
        if score <= 70:
            return "needs_practice"
        return "mastered"
