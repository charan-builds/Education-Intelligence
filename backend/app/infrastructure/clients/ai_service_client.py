from __future__ import annotations

import hashlib
import json
import time

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import ai_request_latency_seconds, ai_requests_total
from app.infrastructure.cache.cache_service import CacheService


class AIServiceClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: float = 5.0):
        settings = get_settings()
        self.base_url = (base_url or settings.ai_service_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.ai_service_timeout_seconds
        self.cache_service = CacheService()
        self.logger = get_logger()

    @staticmethod
    def _cache_key(namespace: str, payload: dict) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=True)
        return f"ai-service:{namespace}:{hashlib.sha256(raw.encode('utf-8')).hexdigest()}"

    @staticmethod
    def _context_namespace(*, tenant_id: int, user_id: int) -> str:
        return f"ai-context:user:{tenant_id}:{user_id}"

    async def _cache_scope_payload(
        self,
        *,
        endpoint: str,
        payload: dict,
        tenant_id: int | None = None,
        user_id: int | None = None,
        context_updated_at: str | None = None,
    ) -> dict:
        scoped = {"endpoint": endpoint, "payload": payload}
        if tenant_id is None or user_id is None:
            return scoped
        scoped["tenant_id"] = int(tenant_id)
        scoped["user_id"] = int(user_id)
        scoped["context_version"] = await self.cache_service.namespace_version(self._context_namespace(tenant_id=tenant_id, user_id=user_id))
        if context_updated_at:
            scoped["context_updated_at"] = str(context_updated_at)
        return scoped

    async def invalidate_user_context(self, *, tenant_id: int, user_id: int) -> int:
        return await self.cache_service.bump_namespace_version(self._context_namespace(tenant_id=tenant_id, user_id=user_id))

    @staticmethod
    def _trim_text(value: str, *, limit: int) -> str:
        text = value.strip()
        return text[:limit]

    def _compact_chat_history(self, chat_history: list[dict] | None) -> list[dict[str, str]]:
        trimmed: list[dict[str, str]] = []
        for item in list(chat_history or [])[-4:]:
            role = self._trim_text(str(item.get("role") or "user"), limit=24) or "user"
            content = self._trim_text(str(item.get("content") or ""), limit=320)
            if content:
                trimmed.append({"role": role, "content": content})
        return trimmed

    def _compact_roadmap(self, roadmap: list[dict] | None) -> list[dict]:
        items = list(roadmap or [])
        items.sort(key=lambda item: (int(item.get("priority", 9999)), str(item.get("progress_status", ""))))
        compacted: list[dict] = []
        for item in items[:8]:
            compacted.append(
                {
                    "topic_id": int(item.get("topic_id", 0)),
                    "progress_status": str(item.get("progress_status") or "pending")[:32],
                    "priority": int(item.get("priority", 0)),
                }
            )
        return compacted

    def _compact_mentor_context(self, mentor_context: dict | None) -> dict:
        context = mentor_context or {}
        roadmap_progress = context.get("roadmap_progress") or {}
        user_profile = context.get("user_profile") or {}
        memory_profile = context.get("memory_profile") or {}
        cognitive_model = context.get("cognitive_model") or {}

        def _topic_slice(items: list[dict] | None, *, limit: int) -> list[dict]:
            result: list[dict] = []
            for item in list(items or [])[:limit]:
                result.append(
                    {
                        "topic_id": int(item.get("topic_id", 0)),
                        "topic_name": self._trim_text(str(item.get("topic_name") or ""), limit=80),
                        "score": float(item.get("score", 0.0) or 0.0),
                    }
                )
            return result

        recent_activity: list[dict] = []
        for item in list(context.get("recent_activity") or [])[:4]:
            recent_activity.append(
                {
                    "event_type": self._trim_text(str(item.get("event_type") or ""), limit=48),
                    "topic_name": self._trim_text(str(item.get("topic_name") or ""), limit=80),
                    "minutes": float(item.get("minutes", 0.0) or 0.0),
                }
            )

        return {
            "roadmap_progress": {
                "completion_rate": float(roadmap_progress.get("completion_rate", 0.0) or 0.0),
                "completed_steps": int(roadmap_progress.get("completed_steps", 0) or 0),
                "total_steps": int(roadmap_progress.get("total_steps", 0) or 0),
                "overdue_steps": int(roadmap_progress.get("overdue_steps", 0) or 0),
            },
            "user_profile": {
                "preferred_learning_style": self._trim_text(str(user_profile.get("preferred_learning_style") or ""), limit=48),
                "learning_speed": float(user_profile.get("learning_speed", 0.0) or 0.0),
            },
            "weak_topics": _topic_slice(context.get("weak_topics"), limit=4),
            "strong_topics": _topic_slice(context.get("strong_topics"), limit=2),
            "recent_activity": recent_activity,
            "memory_profile": {
                "learner_summary": self._trim_text(str(memory_profile.get("learner_summary") or ""), limit=240),
                "past_mistakes": [self._trim_text(str(item), limit=120) for item in list(memory_profile.get("past_mistakes") or [])[:3]],
                "improvement_signals": [
                    self._trim_text(str(item), limit=120) for item in list(memory_profile.get("improvement_signals") or [])[:3]
                ],
                "last_session_summary": self._trim_text(str(memory_profile.get("last_session_summary") or ""), limit=180),
            },
            "cognitive_model": {
                "confusion_level": self._trim_text(str(cognitive_model.get("confusion_level") or ""), limit=32),
                "teaching_style": self._trim_text(str(cognitive_model.get("teaching_style") or ""), limit=160),
                "adaptive_actions": [self._trim_text(str(item), limit=120) for item in list(cognitive_model.get("adaptive_actions") or [])[:3]],
            },
        }

    async def _post(
        self,
        endpoint: str,
        *,
        payload: dict,
        cache_ttl: int = 300,
        tenant_id: int | None = None,
        user_id: int | None = None,
        context_updated_at: str | None = None,
    ) -> dict:
        cache_scope = await self._cache_scope_payload(
            endpoint=endpoint,
            payload=payload,
            tenant_id=tenant_id,
            user_id=user_id,
            context_updated_at=context_updated_at,
        )
        cache_key = self._cache_key(endpoint, cache_scope)
        cached = await self.cache_service.get(cache_key)
        if isinstance(cached, dict):
            ai_requests_total.labels(endpoint=endpoint, provider="cache", outcome="hit").inc()
            return cached

        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.post(f"{self.base_url}{endpoint}", json=payload)
                response.raise_for_status()
                data = response.json()
                normalized = data if isinstance(data, dict) else {}
                latency_seconds = time.perf_counter() - started
                provider = str(normalized.get("provider") or "unknown")
                normalized.setdefault("latency_ms", round(latency_seconds * 1000, 2))
                ai_request_latency_seconds.labels(endpoint=endpoint, provider=provider).observe(latency_seconds)
                ai_requests_total.labels(endpoint=endpoint, provider=provider, outcome="ok").inc()
                self.logger.info(
                    "ai_service_request_completed",
                    extra={
                        "log_data": {
                            "endpoint": endpoint,
                            "provider": provider,
                            "latency_ms": normalized.get("latency_ms"),
                            "cached": False,
                        }
                    },
                )
                await self.cache_service.set(cache_key, normalized, ttl=cache_ttl)
                return normalized
            except Exception as exc:
                latency_seconds = time.perf_counter() - started
                ai_request_latency_seconds.labels(endpoint=endpoint, provider="error").observe(latency_seconds)
                ai_requests_total.labels(endpoint=endpoint, provider="error", outcome="error").inc()
                self.logger.error(
                    "ai_service_request_failed",
                    extra={
                        "log_data": {
                            "endpoint": endpoint,
                            "latency_ms": round(latency_seconds * 1000, 2),
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
                    },
                )
                raise

    async def mentor_response(
        self,
        *,
        user_id: int,
        tenant_id: int,
        goal: str | None,
        message: str,
        roadmap: list[dict],
        weak_topics: list[int],
        learning_profile: dict,
        mentor_context: dict | None = None,
        chat_history: list[dict] | None = None,
    ) -> dict:
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "goal": goal,
            "message": self._trim_text(message, limit=1200),
            "roadmap": self._compact_roadmap(roadmap),
            "weak_topics": [int(topic_id) for topic_id in weak_topics[:5]],
            "learning_profile": {
                "profile_type": str(learning_profile.get("profile_type") or "balanced"),
                "confidence": float(learning_profile.get("confidence", 0.0) or 0.0),
                "speed": float(learning_profile.get("speed", 0.0) or 0.0),
                "accuracy": float(learning_profile.get("accuracy", 0.0) or 0.0),
                "consistency": float(learning_profile.get("consistency", 0.0) or 0.0),
            },
            "mentor_context": self._compact_mentor_context(mentor_context),
            "chat_history": self._compact_chat_history(chat_history),
        }
        return await self._post("/ai/mentor-chat", payload=payload, cache_ttl=90, tenant_id=tenant_id, user_id=user_id)

    async def predict_learning_path(
        self,
        *,
        user_id: int,
        tenant_id: int,
        goal: str,
        topic_scores: dict[int, float],
        prerequisites: list[tuple[int, int]] | None = None,
        learning_profile: dict,
    ) -> dict:
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "goal": goal,
            "topic_scores": [
                {"topic_id": int(topic_id), "score": float(score)}
                for topic_id, score in sorted(topic_scores.items(), key=lambda kv: kv[0])
            ],
            "prerequisites": prerequisites or [],
            "learning_profile": learning_profile,
        }
        return await self._post("/ai/generate-roadmap", payload=payload, cache_ttl=300, tenant_id=tenant_id, user_id=user_id)

    async def analyze_progress(
        self,
        *,
        user_id: int,
        tenant_id: int,
        completion_percent: float,
        weak_topics: list[int],
    ) -> dict:
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "completion_percent": float(completion_percent),
            "weak_topics": weak_topics,
        }
        return await self._post("/ai/analyze-progress", payload=payload, cache_ttl=120, tenant_id=tenant_id, user_id=user_id)

    async def explain_topic(self, *, topic_name: str) -> dict:
        return await self._post("/ai/explain-topic", payload={"topic_name": topic_name}, cache_ttl=1800)

    async def generate_questions(self, *, topic: str, difficulty: str, count: int = 3) -> dict:
        return await self._post(
            "/ai/generate-questions",
            payload={"topic": topic, "difficulty": difficulty, "count": count},
            cache_ttl=900,
        )
