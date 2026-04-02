from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ai_request_service import AIRequestService
from app.application.services.mentor_service import MentorService
from app.infrastructure.repositories.mentor_message_repository import MentorMessageRepository


class AIChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mentor_service = MentorService(session=session)
        self.mentor_message_repository = MentorMessageRepository(session)
        self.ai_request_service = AIRequestService(session)

    async def history(self, *, tenant_id: int, user_id: int, limit: int = 20) -> list[dict]:
        messages = await self.mentor_message_repository.list_recent_messages(
            tenant_id=tenant_id,
            user_id=user_id,
            limit=limit,
        )
        return [
            {
                "request_id": item.request_id,
                "role": item.role,
                "message": item.message,
                "response": item.response,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in messages
        ]

    async def chat(
        self,
        *,
        tenant_id: int,
        user_id: int,
        message: str,
        chat_history: list[dict[str, str]] | None = None,
    ) -> dict:
        normalized_history = list(chat_history or [])
        prompt_context = await self._build_prompt_context(tenant_id=tenant_id, user_id=user_id, message=message)
        queued = await self.ai_request_service.queue_ai_chat(
            tenant_id=tenant_id,
            user_id=user_id,
            message=message,
            chat_history=normalized_history,
        )

        return {
            "request_id": str(queued["request_id"]),
            "status": "processing",
            "reply": "",
            "advisor_type": "queued",
            "used_ai": False,
            "suggested_focus_topics": [],
            "why_recommended": [],
            "provider": None,
            "next_checkin_date": None,
            "session_summary": "AI request is being processed asynchronously.",
            "memory_summary": {},
            "prompt_context": prompt_context,
            "history": await self.history(tenant_id=tenant_id, user_id=user_id),
        }

    async def _build_prompt_context(self, *, tenant_id: int, user_id: int, message: str) -> dict:
        context = await self.mentor_service._load_user_context(user_id=user_id, tenant_id=tenant_id)
        if context is None:
            return {
                "system_role": "AI mentor",
                "goal": "Explain topics and suggest next actions.",
                "message": message,
                "roadmap": {},
                "weak_topics": [],
            }

        weak_topics = context.missing_foundations or sorted(
            topic_id for topic_id, score in context.topic_scores.items() if score < 70.0
        )
        next_topics = [
            int(step.topic_id)
            for step in sorted(context.steps, key=lambda item: int(item.priority))
            if str(step.progress_status).lower() != "completed"
        ][:3]
        return {
            "system_role": "AI mentor",
            "goal": "Chat with the learner, explain topics clearly, and suggest the best next roadmap topic.",
            "message": message,
            "roadmap": {
                "completion_rate": round(float(context.completion_rate), 2),
                "completed_steps": int(context.completed_steps),
                "total_steps": len(context.steps),
                "next_topics": next_topics,
            },
            "weak_topics": weak_topics[:5],
            "learning_profile": dict(context.learning_profile),
        }
