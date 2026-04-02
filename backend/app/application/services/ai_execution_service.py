from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.application.services.mentor_ai_service import MentorAIService
from app.infrastructure.clients.ai_service_client import AIServiceClient


class AIRequestExecutor(Protocol):
    async def execute(self, *, payload: dict, tenant_id: int, user_id: int, steps: list | None = None) -> dict: ...


@dataclass
class MentorChatExecutor:
    mentor_ai_service: MentorAIService

    async def execute(self, *, payload: dict, tenant_id: int, user_id: int, steps: list | None = None) -> dict:
        return await self.mentor_ai_service.generate_response(
            user_id=user_id,
            tenant_id=tenant_id,
            goal=None,
            message=str(payload["message"]),
            steps=list(steps or []),
            weak_topics=[
                int(topic_id)
                for topic_id in list(payload.get("weak_topics") or [])
                if str(topic_id).isdigit() or isinstance(topic_id, int)
            ],
            learning_profile=dict(payload.get("learning_profile") or {}),
            mentor_context=payload.get("mentor_context") if isinstance(payload.get("mentor_context"), dict) else None,
            chat_history=list(payload.get("chat_history") or []),
        )


@dataclass
class TopicExplanationExecutor:
    ai_service_client: AIServiceClient

    async def execute(self, *, payload: dict, tenant_id: int, user_id: int, steps: list | None = None) -> dict:
        return await self.ai_service_client.explain_topic(topic_name=str(payload["topic_name"]))


@dataclass
class TopicQuestionGenerationExecutor:
    ai_service_client: AIServiceClient

    async def execute(self, *, payload: dict, tenant_id: int, user_id: int, steps: list | None = None) -> dict:
        return await self.ai_service_client.generate_questions(
            topic=str(payload["topic"]),
            difficulty=str(payload["difficulty"]),
            count=int(payload["count"]),
        )


@dataclass
class CareerInterviewPrepExecutor:
    ai_service_client: AIServiceClient

    async def execute(self, *, payload: dict, tenant_id: int, user_id: int, steps: list | None = None) -> dict:
        return await self.ai_service_client.generate_questions(
            topic=str(payload["role_name"]),
            difficulty=str(payload["difficulty"]),
            count=int(payload["count"]),
        )


@dataclass
class MentorProgressAnalysisExecutor:
    ai_service_client: AIServiceClient

    async def execute(self, *, payload: dict, tenant_id: int, user_id: int, steps: list | None = None) -> dict:
        return await self.ai_service_client.analyze_progress(
            user_id=user_id,
            tenant_id=tenant_id,
            completion_percent=float(payload["completion_percent"]),
            weak_topics=[int(topic_id) for topic_id in list(payload.get("weak_topics") or [])],
        )


@dataclass
class LearningPathRecommendationExecutor:
    ai_service_client: AIServiceClient

    async def execute(self, *, payload: dict, tenant_id: int, user_id: int, steps: list | None = None) -> dict:
        return await self.ai_service_client.predict_learning_path(
            user_id=user_id,
            tenant_id=tenant_id,
            goal=str(payload["goal"]),
            topic_scores={
                int(topic_id): float(score)
                for topic_id, score in dict(payload.get("topic_scores") or {}).items()
            },
            prerequisites=[
                (int(item[0]), int(item[1]))
                for item in list(payload.get("prerequisites") or [])
                if isinstance(item, (list, tuple)) and len(item) == 2
            ],
            learning_profile=dict(payload.get("learning_profile") or {}),
        )


class AIExecutionService:
    def __init__(
        self,
        *,
        ai_service_client: AIServiceClient | None = None,
        mentor_ai_service: MentorAIService | None = None,
    ) -> None:
        shared_ai_service_client = ai_service_client or AIServiceClient()
        shared_mentor_ai_service = mentor_ai_service or MentorAIService(ai_service_client=shared_ai_service_client)
        self.executors: dict[str, AIRequestExecutor] = {
            "mentor_chat": MentorChatExecutor(mentor_ai_service=shared_mentor_ai_service),
            "ai_chat": MentorChatExecutor(mentor_ai_service=shared_mentor_ai_service),
            "topic_explanation": TopicExplanationExecutor(ai_service_client=shared_ai_service_client),
            "topic_question_generation": TopicQuestionGenerationExecutor(ai_service_client=shared_ai_service_client),
            "career_interview_prep": CareerInterviewPrepExecutor(ai_service_client=shared_ai_service_client),
            "mentor_progress_analysis": MentorProgressAnalysisExecutor(ai_service_client=shared_ai_service_client),
            "learning_path_recommendation": LearningPathRecommendationExecutor(ai_service_client=shared_ai_service_client),
        }

    async def execute(self, *, request_type: str, payload: dict, tenant_id: int, user_id: int, steps: list | None = None) -> dict:
        executor = self.executors.get(request_type)
        if executor is None:
            raise ValueError(f"Unsupported AI request type: {request_type}")
        return await executor.execute(
            payload=payload,
            tenant_id=tenant_id,
            user_id=user_id,
            steps=steps,
        )
