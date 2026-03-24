from __future__ import annotations

import hashlib
import json

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
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

    async def _post(self, endpoint: str, *, payload: dict, cache_ttl: int = 300) -> dict:
        cache_key = self._cache_key(endpoint, payload)
        cached = await self.cache_service.get(cache_key)
        if isinstance(cached, dict):
            return cached

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}{endpoint}", json=payload)
            response.raise_for_status()
            data = response.json()
            normalized = data if isinstance(data, dict) else {}
            await self.cache_service.set(cache_key, normalized, ttl=cache_ttl)
            return normalized

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
            "message": message,
            "roadmap": roadmap,
            "weak_topics": weak_topics,
            "learning_profile": learning_profile,
            "mentor_context": mentor_context or {},
            "chat_history": chat_history or [],
        }
        return await self._post("/ai/mentor-chat", payload=payload, cache_ttl=180)

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
        return await self._post("/ai/generate-roadmap", payload=payload, cache_ttl=900)

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
        return await self._post("/ai/analyze-progress", payload=payload, cache_ttl=300)

    async def explain_topic(self, *, topic_name: str) -> dict:
        return await self._post("/ai/explain-topic", payload={"topic_name": topic_name}, cache_ttl=1800)

    async def generate_questions(self, *, topic: str, difficulty: str, count: int = 3) -> dict:
        return await self._post(
            "/ai/generate-questions",
            payload={"topic": topic, "difficulty": difficulty, "count": count},
            cache_ttl=900,
        )
