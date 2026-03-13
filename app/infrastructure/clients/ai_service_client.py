from __future__ import annotations

import httpx

from app.core.config import get_settings


class AIServiceClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: float = 5.0):
        settings = get_settings()
        self.base_url = (base_url or settings.ai_service_url).rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def mentor_response(
        self,
        *,
        user_id: int,
        tenant_id: int,
        message: str,
        roadmap: list[dict],
        weak_topics: list[int],
        learning_profile: dict,
    ) -> dict:
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "message": message,
            "roadmap": roadmap,
            "weak_topics": weak_topics,
            "learning_profile": learning_profile,
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/mentor-response", json=payload)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {}

    async def predict_learning_path(
        self,
        *,
        user_id: int,
        tenant_id: int,
        goal: str,
        topic_scores: dict[int, float],
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
            "learning_profile": learning_profile,
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/predict-learning-path", json=payload)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {}
