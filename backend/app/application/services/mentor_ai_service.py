from __future__ import annotations

from app.core.logging import bind_log_data, get_logger
from app.infrastructure.clients.ai_service_client import AIServiceClient


class MentorAIService:
    def __init__(self, ai_service_client: AIServiceClient | None = None) -> None:
        self.ai_service_client = ai_service_client or AIServiceClient()
        self.logger = get_logger()

    async def generate_response(
        self,
        *,
        user_id: int,
        tenant_id: int,
        goal: str | None,
        message: str,
        steps: list,
        weak_topics: list[int],
        learning_profile: dict,
        mentor_context: dict | None,
        chat_history: list[dict],
    ) -> dict:
        try:
            roadmap_payload = [
                {
                    "topic_id": int(step.topic_id),
                    "progress_status": str(step.progress_status),
                    "priority": int(step.priority),
                }
                for step in steps
            ]
            result = await self.ai_service_client.mentor_response(
                user_id=user_id,
                tenant_id=tenant_id,
                goal=goal,
                message=message,
                roadmap=roadmap_payload,
                weak_topics=weak_topics,
                learning_profile=learning_profile,
                mentor_context=mentor_context,
                chat_history=chat_history,
            )
            response = result.get("response")
            if not response:
                self.logger.warning("mentor_ai_empty_response", extra=bind_log_data(user_id=user_id, tenant_id=tenant_id))
                return {
                    "reply": None,
                    "fallback_used": True,
                    "fallback_reason": "empty_ai_response",
                    "provider": result.get("provider"),
                    "latency_ms": result.get("latency_ms"),
                }
            return {
                "reply": str(response),
                "fallback_used": bool(result.get("fallback_used")),
                "fallback_reason": result.get("fallback_reason"),
                "suggested_focus_topics": [
                    int(topic_id)
                    for topic_id in result.get("suggested_focus_topics", [])
                    if str(topic_id).isdigit()
                ],
                "why_recommended": [str(item) for item in (result.get("guidance") or {}).get("suggestions", [])][:3],
                "provider": result.get("provider"),
                "latency_ms": result.get("latency_ms"),
                "next_checkin_date": result.get("next_checkin_date"),
                "session_summary": str(result.get("session_summary") or ""),
                "memory_update": result.get("memory_update") if isinstance(result.get("memory_update"), dict) else {},
            }
        except Exception as exc:
            self.logger.error(
                "mentor_ai_request_failed",
                extra=bind_log_data(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    error_type=type(exc).__name__,
                    error=str(exc),
                ),
            )
            return {
                "reply": None,
                "fallback_used": True,
                "fallback_reason": type(exc).__name__,
                "provider": None,
                "latency_ms": None,
            }
