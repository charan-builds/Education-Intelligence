from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import NotFoundError
from app.application.services.recommendation_service import RecommendationService
from app.domain.engines.weakness_modeling_engine import WeaknessModelingEngine
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.repositories.topic_repository import TopicRepository


class DiagnosticAnalysisService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        diagnostic_repository: DiagnosticRepository | None = None,
        topic_repository: TopicRepository | None = None,
        roadmap_repository: RoadmapRepository | None = None,
        weakness_engine: WeaknessModelingEngine | None = None,
        recommendation_service: RecommendationService | None = None,
    ):
        self.session = session
        self.diagnostic_repository = diagnostic_repository or DiagnosticRepository(session)
        self.topic_repository = topic_repository or TopicRepository(session)
        self.roadmap_repository = roadmap_repository or RoadmapRepository(session)
        self.weakness_engine = weakness_engine or WeaknessModelingEngine()
        self.recommendation_service = recommendation_service or RecommendationService(session=session)

    @staticmethod
    def classify_performance(score: float) -> str:
        if score < 50.0:
            return "weak"
        if score <= 70.0:
            return "moderate"
        return "strong"

    async def topic_wise_performance(self, *, test_id: int, user_id: int, tenant_id: int) -> dict[str, dict]:
        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
        if test is None:
            raise NotFoundError("Test not found")

        rows = await self.diagnostic_repository.topic_performance_for_test(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        return {
            row["topic_name"]: {
                "score": row["score_percentage"],
                "level": self.classify_performance(float(row["score_percentage"])),
            }
            for row in rows
        }

    async def detect_knowledge_gaps(self, *, test_id: int, user_id: int, tenant_id: int) -> dict:
        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
        if test is None:
            raise NotFoundError("Test not found")

        topic_scores = await self.diagnostic_repository.topic_scores_for_test(test_id, user_id, tenant_id)
        prerequisite_map = await self._prerequisite_map(tenant_id=tenant_id)
        topic_names = await self._topic_names(
            tenant_id=tenant_id,
            topic_ids=self._topic_ids_for_gap_analysis(topic_scores, prerequisite_map),
        )
        return self.weakness_engine.detect_root_gaps(
            topic_scores={int(topic_id): float(score) for topic_id, score in topic_scores.items()},
            prerequisite_map=prerequisite_map,
            topic_names=topic_names,
        )

    async def get_result(self, test_id: int, user_id: int, tenant_id: int) -> dict:
        scores = await self.diagnostic_repository.topic_scores_for_test(test_id, user_id, tenant_id)
        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
        if not test:
            raise NotFoundError("Test not found")

        roadmap = await self.roadmap_repository.get_by_identity(
            user_id=user_id,
            goal_id=test.goal_id,
            test_id=test_id,
            tenant_id=tenant_id,
        )
        weakness_analysis = self.weakness_engine.analyze(
            topic_scores={int(topic_id): float(score) for topic_id, score in scores.items()},
            prerequisite_map=await self._prerequisite_map(tenant_id=tenant_id),
        )
        foundation_gap_topic_ids = sorted(
            {
                int(prerequisite_topic_id)
                for item in weakness_analysis.get("deep_weaknesses", [])
                for prerequisite_topic_id in item.get("missing_foundations", [])
            }
        )
        recommendation_levels = {
            int(topic_id): self.recommendation_service.engine.classify_topic(float(score))
            for topic_id, score in scores.items()
        }
        return {
            "test_id": test_id,
            "topic_scores": scores,
            "weak_topic_ids": [int(item["topic_id"]) for item in weakness_analysis.get("deep_weaknesses", [])],
            "foundation_gap_topic_ids": foundation_gap_topic_ids,
            "recommendation_levels": recommendation_levels,
            "roadmap": roadmap,
        }

    async def _prerequisite_map(self, *, tenant_id: int) -> dict[int, list[int]]:
        prerequisite_map: dict[int, list[int]] = {}
        for topic_id, prerequisite_topic_id in await self.topic_repository.get_prerequisite_edges(tenant_id=tenant_id):
            prerequisite_map.setdefault(int(topic_id), []).append(int(prerequisite_topic_id))
        return prerequisite_map

    @staticmethod
    def _topic_ids_for_gap_analysis(topic_scores: dict[int, float], prerequisite_map: dict[int, list[int]]) -> list[int]:
        topic_ids = {int(topic_id) for topic_id in topic_scores}
        for topic_id, prerequisite_ids in prerequisite_map.items():
            topic_ids.add(int(topic_id))
            topic_ids.update(int(prerequisite_id) for prerequisite_id in prerequisite_ids)
        return sorted(topic_ids)

    async def _topic_names(self, *, tenant_id: int, topic_ids: list[int]) -> dict[int, str]:
        if not topic_ids or not hasattr(self.topic_repository, "list_topics_by_ids"):
            return {}
        topics = await self.topic_repository.list_topics_by_ids(topic_ids, tenant_id=tenant_id)
        return {int(topic.id): str(topic.name) for topic in topics}
