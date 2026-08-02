from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.adaptive_engine_service import AdaptiveEngineService
from app.application.services.diagnostic import (
    AdaptiveSelectionService,
    DiagnosticAnalysisService,
    DiagnosticCompletionOrchestrator,
    DiagnosticScoringService,
    DiagnosticTestService,
)
from app.application.services.gamification_service import GamificationService
from app.application.services.learning_event_service import LearningEventService
from app.application.services.learning_profile_service import LearningProfileService
from app.application.services.ml_platform_service import MLPlatformService
from app.application.services.outbox_service import OutboxService
from app.application.services.recommendation_service import RecommendationService
from app.application.services.retention_service import RetentionService
from app.application.services.roadmap_service import RoadmapService
from app.application.services.skill_vector_service import SkillVectorService
from app.core.feature_flags import FeatureFlagService
from app.domain.engines.adaptive_testing_engine import AdaptiveTestingEngine
from app.domain.engines.weakness_modeling_engine import WeaknessModelingEngine
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.goal_repository import GoalRepository
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.repositories.topic_repository import TopicRepository


class DiagnosticService:
    """Compatibility facade over the modular diagnostic services.

    New code should depend on the specific service it needs. Existing routes,
    jobs, and tests can keep using this facade while the business workflows live
    in smaller, independently testable classes.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.scoring_service = DiagnosticScoringService()

        self._diagnostic_repository = DiagnosticRepository(session)
        self._topic_repository = TopicRepository(session)
        self._goal_repository = GoalRepository(session)
        self._roadmap_repository = RoadmapRepository(session)

        self._adaptive_engine = AdaptiveTestingEngine()
        self._adaptive_engine_service = AdaptiveEngineService()
        self._weakness_engine = WeaknessModelingEngine()
        self._feature_flag_service = FeatureFlagService(session)
        self._learning_event_service = LearningEventService(session)
        self._outbox_service = OutboxService(session)
        self._gamification_service = GamificationService(session)
        self._retention_service = RetentionService(session)
        self._skill_vector_service = SkillVectorService(session)
        self._ml_platform_service = MLPlatformService(session)
        self._cache_service = CacheService()
        self._recommendation_service = RecommendationService(session=session)
        self._learning_profile_service = LearningProfileService(session)
        self._roadmap_service = RoadmapService(session)

        self.selection_service = AdaptiveSelectionService(
            session,
            diagnostic_repository=self._diagnostic_repository,
            topic_repository=self._topic_repository,
            feature_flag_service=self._feature_flag_service,
            learning_profile_service=self._learning_profile_service,
            weakness_engine=self._weakness_engine,
            adaptive_engine=self._adaptive_engine,
            scoring_service=self.scoring_service,
        )
        self.completion_orchestrator = DiagnosticCompletionOrchestrator(
            session,
            diagnostic_repository=self._diagnostic_repository,
            topic_repository=self._topic_repository,
            selection_service=self.selection_service,
            scoring_service=self.scoring_service,
            adaptive_engine_service=self._adaptive_engine_service,
            learning_event_service=self._learning_event_service,
            outbox_service=self._outbox_service,
            gamification_service=self._gamification_service,
            retention_service=self._retention_service,
            skill_vector_service=self._skill_vector_service,
            ml_platform_service=self._ml_platform_service,
            cache_service=self._cache_service,
            roadmap_service=self._roadmap_service,
        )
        self.test_service = DiagnosticTestService(
            session,
            diagnostic_repository=self._diagnostic_repository,
            topic_repository=self._topic_repository,
            goal_repository=self._goal_repository,
            selection_service=self.selection_service,
            scoring_service=self.scoring_service,
            adaptive_engine_service=self._adaptive_engine_service,
            learning_event_service=self._learning_event_service,
            skill_vector_service=self._skill_vector_service,
            completion_orchestrator=self.completion_orchestrator,
        )
        self.analysis_service = DiagnosticAnalysisService(
            session,
            diagnostic_repository=self._diagnostic_repository,
            topic_repository=self._topic_repository,
            roadmap_repository=self._roadmap_repository,
            weakness_engine=self._weakness_engine,
            recommendation_service=self._recommendation_service,
        )

    def _propagate(self, attr_name: str, value: object) -> None:
        for service_name in (
            "selection_service",
            "completion_orchestrator",
            "test_service",
            "analysis_service",
        ):
            service = getattr(self, service_name, None)
            if service is not None and hasattr(service, attr_name):
                setattr(service, attr_name, value)

    @property
    def diagnostic_repository(self):
        return self._diagnostic_repository

    @diagnostic_repository.setter
    def diagnostic_repository(self, value):
        self._diagnostic_repository = value
        self._propagate("diagnostic_repository", value)

    @property
    def topic_repository(self):
        return self._topic_repository

    @topic_repository.setter
    def topic_repository(self, value):
        self._topic_repository = value
        self._propagate("topic_repository", value)

    @property
    def goal_repository(self):
        return self._goal_repository

    @goal_repository.setter
    def goal_repository(self, value):
        self._goal_repository = value
        self._propagate("goal_repository", value)

    @property
    def roadmap_repository(self):
        return self._roadmap_repository

    @roadmap_repository.setter
    def roadmap_repository(self, value):
        self._roadmap_repository = value
        self._propagate("roadmap_repository", value)

    @property
    def adaptive_engine(self):
        return self._adaptive_engine

    @adaptive_engine.setter
    def adaptive_engine(self, value):
        self._adaptive_engine = value
        self._propagate("adaptive_engine", value)

    @property
    def adaptive_engine_service(self):
        return self._adaptive_engine_service

    @adaptive_engine_service.setter
    def adaptive_engine_service(self, value):
        self._adaptive_engine_service = value
        self._propagate("adaptive_engine_service", value)

    @property
    def weakness_engine(self):
        return self._weakness_engine

    @weakness_engine.setter
    def weakness_engine(self, value):
        self._weakness_engine = value
        self._propagate("weakness_engine", value)

    @property
    def feature_flag_service(self):
        return self._feature_flag_service

    @feature_flag_service.setter
    def feature_flag_service(self, value):
        self._feature_flag_service = value
        self._propagate("feature_flag_service", value)

    @property
    def learning_profile_service(self):
        return self._learning_profile_service

    @learning_profile_service.setter
    def learning_profile_service(self, value):
        self._learning_profile_service = value
        self._propagate("learning_profile_service", value)

    @property
    def recommendation_service(self):
        return self._recommendation_service

    @recommendation_service.setter
    def recommendation_service(self, value):
        self._recommendation_service = value
        self._propagate("recommendation_service", value)

    @property
    def learning_event_service(self):
        return self._learning_event_service

    @learning_event_service.setter
    def learning_event_service(self, value):
        self._learning_event_service = value
        self._propagate("learning_event_service", value)

    @property
    def outbox_service(self):
        return self._outbox_service

    @outbox_service.setter
    def outbox_service(self, value):
        self._outbox_service = value
        self._propagate("outbox_service", value)

    @property
    def gamification_service(self):
        return self._gamification_service

    @gamification_service.setter
    def gamification_service(self, value):
        self._gamification_service = value
        self._propagate("gamification_service", value)

    @property
    def retention_service(self):
        return self._retention_service

    @retention_service.setter
    def retention_service(self, value):
        self._retention_service = value
        self._propagate("retention_service", value)

    @property
    def skill_vector_service(self):
        return self._skill_vector_service

    @skill_vector_service.setter
    def skill_vector_service(self, value):
        self._skill_vector_service = value
        self._propagate("skill_vector_service", value)

    @property
    def ml_platform_service(self):
        return self._ml_platform_service

    @ml_platform_service.setter
    def ml_platform_service(self, value):
        self._ml_platform_service = value
        self._propagate("ml_platform_service", value)

    @property
    def cache_service(self):
        return self._cache_service

    @cache_service.setter
    def cache_service(self, value):
        self._cache_service = value
        self._propagate("cache_service", value)

    @property
    def roadmap_service(self):
        return self._roadmap_service

    @roadmap_service.setter
    def roadmap_service(self, value):
        self._roadmap_service = value
        self._propagate("roadmap_service", value)

    def _score_answer(self, expected_answer: str, user_answer: str, accepted_answers: list[str] | None = None) -> float:
        return self.scoring_service.calculate_score(
            expected_answer=expected_answer,
            user_answer=user_answer,
            accepted_answers=accepted_answers,
        )

    @staticmethod
    def _accuracy_from_score(score: float) -> float:
        return DiagnosticScoringService().accuracy_from_score(score)

    async def start_test(self, user_id: int, goal_id: int, tenant_id: int = 1):
        return await self.test_service.start_test(user_id=user_id, goal_id=goal_id, tenant_id=tenant_id)

    async def start_test_with_questions(
        self,
        *,
        user_id: int,
        goal_id: int,
        tenant_id: int = 1,
        question_count: int = 20,
    ) -> dict:
        return await self.test_service.start_test_with_questions(
            user_id=user_id,
            goal_id=goal_id,
            tenant_id=tenant_id,
            question_count=question_count,
        )

    async def get_or_resume_test(self, *, test_id: int, user_id: int, tenant_id: int):
        return await self.test_service.get_or_resume_test(test_id=test_id, user_id=user_id, tenant_id=tenant_id)

    async def _get_or_build_test_state(
        self,
        *,
        test_id: int,
        user_id: int,
        tenant_id: int,
        for_update: bool = False,
    ):
        return await self.selection_service.get_or_build_test_state(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
            for_update=for_update,
        )

    async def get_next_question(self, *, test_id: int, user_id: int, tenant_id: int) -> dict | None:
        return await self.selection_service.get_next_question(test_id=test_id, user_id=user_id, tenant_id=tenant_id)

    async def answer_question(
        self,
        *,
        test_id: int,
        user_id: int,
        tenant_id: int,
        question_id: int,
        user_answer: str,
        time_taken: float,
    ) -> dict:
        return await self.test_service.answer_question(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
            question_id=question_id,
            user_answer=user_answer,
            time_taken=time_taken,
        )

    async def submit_test(
        self,
        *,
        test_id: int,
        user_id: int,
        tenant_id: int,
        answers: list[dict] | None = None,
        trigger_roadmap: bool = False,
    ) -> dict:
        return await self.test_service.submit_test(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
            answers=answers,
            trigger_roadmap=trigger_roadmap,
        )

    async def submit_answers(self, test_id: int, user_id: int, tenant_id: int, answers: list[dict]) -> dict:
        return await self.completion_orchestrator.submit_answers(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
            answers=answers,
        )

    async def finalize_test(self, *, test_id: int, user_id: int, tenant_id: int) -> dict:
        return await self.completion_orchestrator.finalize_test(test_id=test_id, user_id=user_id, tenant_id=tenant_id)

    async def trigger_roadmap_generation(
        self,
        *,
        user_id: int,
        tenant_id: int,
        goal_id: int,
        test_id: int,
    ) -> bool:
        return await self.completion_orchestrator.trigger_roadmap_generation(
            user_id=user_id,
            tenant_id=tenant_id,
            goal_id=goal_id,
            test_id=test_id,
        )

    async def _questions_by_id(self, *, tenant_id: int, question_ids: list[int]) -> dict[int, object]:
        return await self.completion_orchestrator._questions_by_id(tenant_id=tenant_id, question_ids=question_ids)

    def _build_adaptive_summary(self, *, answers: list[object], questions_by_id: dict[int, object]) -> dict:
        return self.completion_orchestrator.build_adaptive_summary(answers=answers, questions_by_id=questions_by_id)

    @staticmethod
    def _performance_level(score: float) -> str:
        return DiagnosticAnalysisService.classify_performance(score)

    async def analyze_performance(self, *, test_id: int, user_id: int, tenant_id: int) -> dict[str, dict]:
        return await self.analysis_service.topic_wise_performance(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )

    async def detect_knowledge_gaps(self, *, test_id: int, user_id: int, tenant_id: int) -> dict:
        return await self.analysis_service.detect_knowledge_gaps(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )

    async def get_result(self, test_id: int, user_id: int, tenant_id: int) -> dict:
        return await self.analysis_service.get_result(test_id=test_id, user_id=user_id, tenant_id=tenant_id)

    async def select_next_question(
        self,
        goal_id: int,
        previous_answers: list[dict],
        user_id: int | None = None,
        topic_scores: dict[int, float] | None = None,
        question_ids: list[int] | None = None,
        tenant_id: int | None = None,
    ) -> dict | None:
        return await self.selection_service.select_next_question(
            goal_id=goal_id,
            previous_answers=previous_answers,
            user_id=user_id,
            topic_scores=topic_scores,
            question_ids=question_ids,
            tenant_id=tenant_id,
        )
