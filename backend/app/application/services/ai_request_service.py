from __future__ import annotations

import hashlib
import json
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ai_execution_service import AIExecutionService
from app.application.services.mentor_service import MentorService
from app.core.config import get_settings
from app.infrastructure.jobs.dispatcher import enqueue_job_with_options
from app.infrastructure.repositories.ai_request_repository import AIRequestRepository
from app.infrastructure.repositories.mentor_chat_repository import MentorChatRepository
from app.infrastructure.repositories.mentor_message_repository import MentorMessageRepository


class AIRequestService:
    TYPE_MENTOR_CHAT = "mentor_chat"
    TYPE_AI_CHAT = "ai_chat"
    TYPE_TOPIC_EXPLANATION = "topic_explanation"
    TYPE_TOPIC_QUESTION_GENERATION = "topic_question_generation"
    TYPE_CAREER_INTERVIEW_PREP = "career_interview_prep"
    TYPE_MENTOR_PROGRESS_ANALYSIS = "mentor_progress_analysis"
    TYPE_LEARNING_PATH_RECOMMENDATION = "learning_path_recommendation"

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = AIRequestRepository(session)
        self.mentor_chat_repository = MentorChatRepository(session)
        self.mentor_message_repository = MentorMessageRepository(session)
        self.ai_execution_service = AIExecutionService()

    @staticmethod
    def _stable_request_id(*, prefix: str, payload: dict) -> str:
        raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
        return f"{prefix}-{digest}"

    async def _ensure_request(
        self,
        *,
        tenant_id: int,
        user_id: int,
        request_id: str,
        request_type: str,
        payload: dict,
        max_attempts: int = 3,
    ) -> dict:
        existing = await self.repository.get_by_request_id(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
        )
        if existing is None:
            await self.repository.create(
                tenant_id=tenant_id,
                user_id=user_id,
                request_id=request_id,
                request_type=request_type,
                payload=payload,
                max_attempts=max_attempts,
            )
            await self.session.commit()
            enqueue_job_with_options(
                "jobs.process_ai_request",
                kwargs={"tenant_id": tenant_id, "user_id": user_id, "request_id": request_id},
            )
            return {"request_id": request_id, "status": "processing"}

        if existing.status in {"queued", "processing", "failed", "timed_out"}:
            return {"request_id": request_id, "status": "processing"}
        return {"request_id": request_id, "status": str(existing.status)}

    async def queue_mentor_chat(
        self,
        *,
        tenant_id: int,
        user_id: int,
        message: str,
        chat_history: list[dict[str, str]],
        request_id: str | None = None,
        channel: str = "http",
    ) -> dict:
        effective_request_id = request_id or f"mentor-{uuid4().hex}"
        existing = await self.repository.get_by_request_id(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=effective_request_id,
        )
        if existing is None:
            await self.repository.create(
                tenant_id=tenant_id,
                user_id=user_id,
                request_id=effective_request_id,
                request_type=self.TYPE_MENTOR_CHAT,
                payload={"message": message, "chat_history": list(chat_history or []), "channel": channel},
            )
            await self.mentor_chat_repository.upsert_message(
                tenant_id=tenant_id,
                user_id=user_id,
                request_id=effective_request_id,
                direction="inbound",
                channel=channel,
                status="received",
                content=message,
                response_json={"chat_history": chat_history},
            )
            await self.mentor_message_repository.create_message(
                tenant_id=tenant_id,
                user_id=user_id,
                request_id=effective_request_id,
                role="learner",
                message=message,
            )
            await self.session.commit()
            enqueue_job_with_options(
                "jobs.process_ai_request",
                kwargs={"tenant_id": tenant_id, "user_id": user_id, "request_id": effective_request_id},
            )
        return {"request_id": effective_request_id, "status": "processing"}

    async def queue_ai_chat(
        self,
        *,
        tenant_id: int,
        user_id: int,
        message: str,
        chat_history: list[dict[str, str]],
    ) -> dict:
        request_id = f"ai-{uuid4().hex}"
        await self.repository.create(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            request_type=self.TYPE_AI_CHAT,
            payload={"message": message, "chat_history": list(chat_history or [])},
        )
        await self.mentor_message_repository.create_message(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            role="learner",
            message=message,
        )
        await self.session.commit()
        enqueue_job_with_options(
            "jobs.process_ai_request",
            kwargs={"tenant_id": tenant_id, "user_id": user_id, "request_id": request_id},
        )
        return {"request_id": request_id, "status": "processing"}

    async def queue_topic_explanation(
        self,
        *,
        tenant_id: int,
        user_id: int,
        topic_name: str,
    ) -> dict:
        payload = {"topic_name": topic_name.strip()}
        request_id = self._stable_request_id(prefix="topic-explain", payload={"tenant_id": tenant_id, "user_id": user_id, **payload})
        return await self._ensure_request(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            request_type=self.TYPE_TOPIC_EXPLANATION,
            payload=payload,
        )

    async def queue_topic_question_generation(
        self,
        *,
        tenant_id: int,
        user_id: int,
        topic: str,
        difficulty: str,
        count: int,
    ) -> dict:
        payload = {"topic": topic.strip(), "difficulty": difficulty.strip(), "count": int(count)}
        request_id = self._stable_request_id(prefix="topic-questions", payload={"tenant_id": tenant_id, "user_id": user_id, **payload})
        return await self._ensure_request(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            request_type=self.TYPE_TOPIC_QUESTION_GENERATION,
            payload=payload,
        )

    async def queue_career_interview_prep(
        self,
        *,
        tenant_id: int,
        user_id: int,
        role_name: str,
        difficulty: str,
        count: int,
    ) -> dict:
        payload = {"role_name": role_name.strip(), "difficulty": difficulty.strip(), "count": int(count)}
        request_id = self._stable_request_id(prefix="career-interview", payload={"tenant_id": tenant_id, "user_id": user_id, **payload})
        return await self._ensure_request(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            request_type=self.TYPE_CAREER_INTERVIEW_PREP,
            payload=payload,
        )

    async def queue_mentor_progress_analysis(
        self,
        *,
        tenant_id: int,
        user_id: int,
        completion_percent: float,
        weak_topics: list[int],
    ) -> dict:
        payload = {
            "completion_percent": float(completion_percent),
            "weak_topics": [int(topic_id) for topic_id in weak_topics[:5]],
        }
        request_id = self._stable_request_id(prefix="mentor-progress", payload={"tenant_id": tenant_id, "user_id": user_id, **payload})
        return await self._ensure_request(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            request_type=self.TYPE_MENTOR_PROGRESS_ANALYSIS,
            payload=payload,
        )

    async def queue_learning_path_recommendation(
        self,
        *,
        tenant_id: int,
        user_id: int,
        goal: str,
        topic_scores: dict[int, float],
        prerequisites: list[tuple[int, int]] | None,
        learning_profile: dict | None = None,
    ) -> dict:
        payload = {
            "goal": goal.strip(),
            "topic_scores": {str(topic_id): float(score) for topic_id, score in sorted(topic_scores.items(), key=lambda kv: kv[0])},
            "prerequisites": [[int(topic_id), int(prerequisite_topic_id)] for topic_id, prerequisite_topic_id in list(prerequisites or [])],
            "learning_profile": dict(learning_profile or {}),
        }
        request_id = self._stable_request_id(
            prefix="learning-path",
            payload={"tenant_id": tenant_id, "user_id": user_id, **payload},
        )
        return await self._ensure_request(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            request_type=self.TYPE_LEARNING_PATH_RECOMMENDATION,
            payload=payload,
        )

    async def get_result(self, *, tenant_id: int, user_id: int, request_id: str) -> dict | None:
        row = await self.repository.get_by_request_id(tenant_id=tenant_id, user_id=user_id, request_id=request_id)
        if row is None:
            return None
        result = {}
        if row.result_json:
            try:
                parsed = json.loads(row.result_json)
                if isinstance(parsed, dict):
                    result = parsed
            except json.JSONDecodeError:
                result = {}
        return {
            "request_id": row.request_id,
            "request_type": row.request_type,
            "status": row.status,
            "provider": row.provider,
            "attempt_count": int(row.attempt_count),
            "error_message": row.error_message,
            "result": result,
        }

    async def process_request(self, *, tenant_id: int, user_id: int, request_id: str) -> dict:
        row = await self.repository.get_by_request_id(tenant_id=tenant_id, user_id=user_id, request_id=request_id)
        if row is None:
            return {"status": "missing", "request_id": request_id}
        if row.status in {"completed", "fallback"}:
            return {"status": row.status, "request_id": request_id}

        await self.repository.mark_processing(row)
        await self.session.commit()

        payload = json.loads(row.payload_json)
        service = MentorService(session=self.session)
        timeout_seconds = float(get_settings().ai_service_timeout_seconds)

        try:
            if row.request_type in {self.TYPE_MENTOR_CHAT, self.TYPE_AI_CHAT}:
                context = await service._load_user_context(user_id=user_id, tenant_id=tenant_id)
                steps = list(getattr(context, "steps", []) or [])
                weak_topics = []
                learning_profile = {}
                mentor_context = None
                if context is not None:
                    weak_topics = context.missing_foundations or sorted(
                        topic_id for topic_id, score in context.topic_scores.items() if score < 70.0
                    )
                    learning_profile = dict(context.learning_profile)
                    if service.ai_context_builder is not None:
                        mentor_context = await service.ai_context_builder.build_mentor_context(
                            user_id=user_id,
                            tenant_id=tenant_id,
                            learning_profile=context.learning_profile,
                            roadmap_progress={
                                "completion_rate": context.completion_rate,
                                "completed_steps": context.completed_steps,
                                "total_steps": len(context.steps),
                                "overdue_steps": context.overdue_steps,
                            },
                            weak_topics=weak_topics,
                            topic_scores=context.topic_scores,
                            cognitive_model=context.cognitive_model,
                        )
                enriched_payload = {
                    **payload,
                    "weak_topics": weak_topics[:5],
                    "learning_profile": learning_profile,
                    "mentor_context": mentor_context,
                }
                result = await self.ai_execution_service.execute(
                    request_type=row.request_type,
                    payload=enriched_payload,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    steps=steps,
                )
            else:
                result = await self.ai_execution_service.execute(
                    request_type=row.request_type,
                    payload=payload,
                    tenant_id=tenant_id,
                    user_id=user_id,
                )

            if row.request_type == self.TYPE_MENTOR_CHAT:
                outbound = await self.mentor_chat_repository.upsert_message(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    request_id=request_id,
                    direction="outbound",
                    channel=str(payload.get("channel") or "http"),
                    status="ready",
                    content=str(result.get("reply") or ""),
                    response_json=result,
                )
                await self.mentor_chat_repository.mark_delivered(outbound)
            if row.request_type in {self.TYPE_MENTOR_CHAT, self.TYPE_AI_CHAT}:
                await self.mentor_message_repository.set_response(
                    request_id=request_id,
                    response=str(result.get("reply") or ""),
                    status="sent",
                )
            if bool(result.get("fallback_used")):
                await self.repository.mark_fallback(
                    row,
                    result=result,
                    error_message=str(result.get("fallback_reason") or "fallback_used"),
                )
            else:
                await self.repository.mark_completed(row, result=result, provider=result.get("provider"))
            await self.session.commit()
            return {"status": row.status, "request_id": request_id}
        except TimeoutError as exc:
            if int(row.attempt_count) < int(row.max_attempts):
                delay_seconds = int(timeout_seconds * max(1, 2 ** max(int(row.attempt_count) - 1, 0)))
                enqueue_job_with_options(
                    "jobs.process_ai_request",
                    kwargs={"tenant_id": tenant_id, "user_id": user_id, "request_id": request_id},
                    countdown=delay_seconds,
                )
                await self.repository.mark_failed(row, error_message=str(exc), timed_out=True)
                await self.session.commit()
                return {"status": "retry_scheduled", "request_id": request_id}
            fallback = self._fallback_result(request_type=row.request_type, payload=payload)
            await self.repository.mark_fallback(row, result=fallback, error_message="timeout")
            await self.session.commit()
            return {"status": "fallback", "request_id": request_id}
        except Exception as exc:
            if int(row.attempt_count) < int(row.max_attempts):
                delay_seconds = 30 * (2 ** max(int(row.attempt_count) - 1, 0))
                enqueue_job_with_options(
                    "jobs.process_ai_request",
                    kwargs={"tenant_id": tenant_id, "user_id": user_id, "request_id": request_id},
                    countdown=delay_seconds,
                )
                await self.repository.mark_failed(row, error_message=str(exc))
                await self.session.commit()
                return {"status": "retry_scheduled", "request_id": request_id}
            fallback = self._fallback_result(request_type=row.request_type, payload=payload)
            await self.repository.mark_fallback(row, result=fallback, error_message=str(exc))
            await self.session.commit()
            return {"status": "fallback", "request_id": request_id}

    @staticmethod
    def _fallback_result(*, request_type: str, payload: dict) -> dict:
        if request_type in {AIRequestService.TYPE_MENTOR_CHAT, AIRequestService.TYPE_AI_CHAT}:
            message = str(payload.get("message") or "")
            return {
                "reply": (
                    "AI is temporarily unavailable. Focus on one weak topic, complete one pending roadmap step, "
                    f"and capture one takeaway from: '{message[:180]}'"
                ),
                "advisor_type": "fallback",
                "used_ai": False,
                "fallback_used": True,
                "fallback_reason": "ai_unavailable",
                "suggested_focus_topics": [],
                "why_recommended": ["Fallback guidance was returned because the AI service was unavailable."],
                "provider": None,
                "latency_ms": None,
                "next_checkin_date": None,
                "session_summary": "",
                "memory_summary": {},
            }
        if request_type == AIRequestService.TYPE_TOPIC_EXPLANATION:
            topic_name = str(payload.get("topic_name") or "this topic")
            return {
                "topic_name": topic_name,
                "explanation": f"A detailed explanation for {topic_name} is being prepared. Start with the core definition, one example, and one practical use case.",
                "examples": [f"Core example for {topic_name}"],
                "use_cases": [f"Practical use case for {topic_name}"],
                "guidance": {
                    "suggestions": ["Review the topic summary and revisit prerequisite concepts."],
                    "next_steps": ["Check back shortly for the full AI-generated explanation."],
                },
                "fallback_used": True,
                "provider": None,
            }
        if request_type in {AIRequestService.TYPE_TOPIC_QUESTION_GENERATION, AIRequestService.TYPE_CAREER_INTERVIEW_PREP}:
            topic = str(payload.get("topic") or payload.get("role_name") or "topic")
            difficulty = str(payload.get("difficulty") or "intermediate")
            return {
                "topic": topic,
                "difficulty": difficulty,
                "questions": [],
                "guidance": {
                    "suggestions": ["Question generation is queued; use existing practice material in the meantime."],
                    "next_steps": ["Check back shortly for generated questions."],
                },
                "fallback_used": True,
                "provider": None,
            }
        if request_type == AIRequestService.TYPE_MENTOR_PROGRESS_ANALYSIS:
            return {
                "summary": "Progress analysis is being refreshed asynchronously.",
                "recommended_focus_topics": list(payload.get("weak_topics") or []),
                "guidance": {
                    "suggestions": ["Continue with your next roadmap step while the AI summary is generated."],
                },
                "fallback_used": True,
                "provider": None,
            }
        if request_type == AIRequestService.TYPE_LEARNING_PATH_RECOMMENDATION:
            topic_scores = {
                int(topic_id): float(score)
                for topic_id, score in dict(payload.get("topic_scores") or {}).items()
            }
            ordered_topics = [topic_id for topic_id, _ in sorted(topic_scores.items(), key=lambda kv: (kv[1], kv[0]))]
            return {
                "recommended_steps": [{"topic_id": int(topic_id)} for topic_id in ordered_topics[:10]],
                "fallback_used": True,
                "provider": None,
            }
        return {"fallback_used": True, "provider": None}
