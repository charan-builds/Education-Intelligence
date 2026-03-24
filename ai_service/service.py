from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from ai_service.cache import TTLCache
from ai_service.config import AISettings
from ai_service.guardrails import injection_hints, safe_topic_name, sanitize_text
from ai_service.llm_client import LLMClient
from ai_service.prompts import (
    explain_topic_prompt,
    generate_questions_prompt,
    mentor_chat_prompt,
    progress_prompt,
    roadmap_prompt,
)
from ai_service.schemas import (
    LearningPathRequest,
    LearningPathResponse,
    LearningPathStep,
    MentorResponse,
    MentorResponseRequest,
    ProgressAnalysisRequest,
    ProgressAnalysisResponse,
    PromptSection,
    QuestionGenerationRequest,
    QuestionGenerationResponse,
    TopicExplainRequest,
    TopicExplainResponse,
)

logger = logging.getLogger("ai_service.service")


class AIOrchestrator:
    def __init__(self, settings: AISettings):
        self.settings = settings
        self.cache = TTLCache()
        self.llm = LLMClient(settings)

    @staticmethod
    def _guidance(data: dict[str, Any]) -> PromptSection:
        guidance = data.get("guidance") or {}
        return PromptSection(
            explanation=str(guidance.get("explanation") or ""),
            suggestions=[str(item) for item in guidance.get("suggestions", [])][:5],
            next_steps=[str(item) for item in guidance.get("next_steps", [])][:5],
        )

    def _safe_context(self, payload: dict[str, Any]) -> dict[str, Any]:
        cleaned = dict(payload)
        if "message" in cleaned:
            cleaned["message"] = sanitize_text(str(cleaned["message"]), limit=self.settings.ai_request_max_input_chars)
            cleaned["message_injection_hints"] = injection_hints(cleaned["message"])
        if "chat_history" in cleaned:
            trimmed_history: list[dict[str, str]] = []
            for item in list(cleaned.get("chat_history") or [])[-self.settings.ai_chat_history_limit :]:
                role = str(item.get("role") or "user")[:32]
                content = sanitize_text(str(item.get("content") or ""), limit=600)
                if content:
                    trimmed_history.append({"role": role, "content": content})
            cleaned["chat_history"] = trimmed_history
            if trimmed_history:
                cleaned["chat_history_summary"] = " | ".join(
                    f"{entry['role']}: {entry['content'][:120]}" for entry in trimmed_history[-3:]
                )
        if "topic_name" in cleaned:
            cleaned["topic_name"] = safe_topic_name(str(cleaned["topic_name"]))
        if "topic" in cleaned:
            cleaned["topic"] = safe_topic_name(str(cleaned["topic"]))
        return cleaned

    async def mentor_chat(self, payload: MentorResponseRequest) -> MentorResponse:
        context = self._safe_context(payload.model_dump())
        cache_key = self.cache.make_key("mentor_chat", context)
        cached = self.cache.get(cache_key)
        if cached:
            return MentorResponse(**cached)

        fallback_topics = sorted(set(payload.weak_topics))[:5]
        if not self.llm.enabled:
            weak_topics = [
                str(item.get("topic_name") or item.get("topic_id"))
                for item in (payload.mentor_context.get("weak_topics") or [])
            ][:5]
            strong_topics = [
                str(item.get("topic_name") or item.get("topic_id"))
                for item in (payload.mentor_context.get("strong_topics") or [])
            ][:5]
            result = MentorResponse(
                user_id=payload.user_id,
                tenant_id=payload.tenant_id,
                response=(
                    "Focus first on your weakest topics, keep sessions short and consistent, "
                    "and finish one roadmap action before branching out."
                ),
                suggested_focus_topics=fallback_topics,
                provider=None,
                next_checkin_date=date.today() + timedelta(days=7),
                guidance=PromptSection(
                    explanation="No LLM provider is configured, so fallback mentor guidance was used.",
                    suggestions=["Review one weak topic.", "Finish one roadmap step.", "Write down one takeaway."],
                    next_steps=["Come back after your next study session."],
                ),
                session_summary=f"Discussed '{payload.message[:120]}' with focus on {', '.join(weak_topics) if weak_topics else 'current weak topics'}.",
                memory_update={
                    "learner_summary": "Learner benefits from concise, actionable tutoring with consistent progress check-ins.",
                    "weak_topics": weak_topics,
                    "strong_topics": strong_topics,
                    "past_mistakes": weak_topics[:3],
                    "improvement_signals": [f"Current completion is {payload.mentor_context.get('roadmap_progress', {}).get('completion_rate', 0)}%."],
                    "preferred_learning_style": str(payload.learning_profile.get("profile_type") or "balanced"),
                    "learning_speed": float(payload.mentor_context.get("user_profile", {}).get("learning_speed") or 0.0),
                    "session_summary": f"Learner asked: {payload.message[:120]}",
                },
            )
            self.cache.set(cache_key, result.model_dump(mode="json"), ttl=120)
            return result

        data = await self.llm.generate_json(
            system_prompt="You are a safe, concise, high-quality learning mentor.",
            user_prompt=mentor_chat_prompt(context),
        )
        guidance = self._guidance(data)
        result = MentorResponse(
            user_id=payload.user_id,
            tenant_id=payload.tenant_id,
            response=str(data.get("response") or ""),
            suggested_focus_topics=[
                int(item) for item in data.get("suggested_focus_topics", []) if str(item).isdigit()
            ][:5],
            provider=str(data.get("_provider")) if data.get("_provider") else None,
            next_checkin_date=date.today() + timedelta(days=7),
            guidance=PromptSection(
                explanation=guidance.explanation,
                suggestions=[
                    *guidance.suggestions[:4],
                    f"Provider: {data.get('_provider', 'unknown')}",
                ][:5],
                next_steps=guidance.next_steps,
            ),
            session_summary=str(data.get("session_summary") or ""),
            memory_update=data.get("memory_update") if isinstance(data.get("memory_update"), dict) else {},
        )
        self.cache.set(cache_key, result.model_dump(mode="json"), ttl=self.settings.ai_cache_ttl_seconds)
        return result

    async def generate_roadmap(self, payload: LearningPathRequest) -> LearningPathResponse:
        context = self._safe_context(payload.model_dump())
        cache_key = self.cache.make_key("generate_roadmap", context)
        cached = self.cache.get(cache_key)
        if cached:
            return LearningPathResponse(**cached)

        if not self.llm.enabled:
            ordered = sorted(payload.topic_scores, key=lambda item: (item.score, item.topic_id))
            result = LearningPathResponse(
                user_id=payload.user_id,
                tenant_id=payload.tenant_id,
                goal=payload.goal,
                strategy="fallback_rule_v2",
                recommended_steps=[
                    LearningPathStep(
                        topic_id=item.topic_id,
                        priority=index,
                        reason="weak_foundation",
                        estimated_time_hours=round(2 + ((100 - item.score) / 20), 2),
                    )
                    for index, item in enumerate(ordered[:10], start=1)
                ],
                reasoning=PromptSection(
                    explanation="Fallback ordering was used because no LLM key is configured.",
                    suggestions=["Start with the weakest prerequisite-backed topic."],
                    next_steps=["Re-run with LLM enabled for richer reasoning."],
                ),
            )
            self.cache.set(cache_key, result.model_dump(mode="json"), ttl=120)
            return result

        data = await self.llm.generate_json(
            system_prompt="You are an expert curriculum planner. Obey prerequisites and keep outputs machine-readable.",
            user_prompt=roadmap_prompt(context),
        )
        raw_steps = data.get("recommended_steps", [])
        steps = []
        for index, item in enumerate(raw_steps, start=1):
            if not isinstance(item, dict) or item.get("topic_id") is None:
                continue
            steps.append(
                LearningPathStep(
                    topic_id=int(item["topic_id"]),
                    priority=int(item.get("priority") or index),
                    reason=str(item.get("reason") or "goal_alignment"),
                    estimated_time_hours=float(item.get("estimated_time_hours") or 4.0),
                )
            )
        result = LearningPathResponse(
            user_id=payload.user_id,
            tenant_id=payload.tenant_id,
            goal=payload.goal,
            strategy=f"openai:{self.settings.openai_model}",
            recommended_steps=steps,
            reasoning=self._guidance(data),
        )
        self.cache.set(cache_key, result.model_dump(mode="json"), ttl=self.settings.ai_cache_ttl_seconds)
        return result

    async def analyze_progress(self, payload: ProgressAnalysisRequest) -> ProgressAnalysisResponse:
        context = self._safe_context(payload.model_dump())
        cache_key = self.cache.make_key("analyze_progress", context)
        cached = self.cache.get(cache_key)
        if cached:
            return ProgressAnalysisResponse(**cached)

        if not self.llm.enabled:
            result = ProgressAnalysisResponse(
                user_id=payload.user_id,
                tenant_id=payload.tenant_id,
                summary=f"Completion is {payload.completion_percent:.1f}%. Keep attention on weak topics.",
                recommended_focus_topics=sorted(set(payload.weak_topics))[:5],
                guidance=PromptSection(
                    explanation="Fallback progress analysis was used because no LLM key is configured.",
                    suggestions=["Address one weak topic this week."],
                    next_steps=["Review your progress after the next milestone."],
                ),
            )
            self.cache.set(cache_key, result.model_dump(mode="json"), ttl=120)
            return result

        data = await self.llm.generate_json(
            system_prompt="You are a learning progress analyst. Summaries should be concise and actionable.",
            user_prompt=progress_prompt(context),
        )
        result = ProgressAnalysisResponse(
            user_id=payload.user_id,
            tenant_id=payload.tenant_id,
            summary=str(data.get("summary") or ""),
            recommended_focus_topics=[
                int(item) for item in data.get("recommended_focus_topics", []) if str(item).isdigit()
            ][:5],
            guidance=self._guidance(data),
        )
        self.cache.set(cache_key, result.model_dump(mode="json"), ttl=self.settings.ai_cache_ttl_seconds)
        return result

    async def explain_topic(self, payload: TopicExplainRequest) -> TopicExplainResponse:
        context = self._safe_context(payload.model_dump())
        cache_key = self.cache.make_key("explain_topic", context)
        cached = self.cache.get(cache_key)
        if cached:
            return TopicExplainResponse(**cached)

        if not self.llm.enabled:
            result = TopicExplainResponse(
                topic_name=payload.topic_name,
                explanation=f"{payload.topic_name} is an important learning topic. Enable an OpenAI API key for richer explanations.",
                examples=[f"Basic example for {payload.topic_name}"],
                use_cases=[f"Use {payload.topic_name} to solve practical learning problems."],
                guidance=PromptSection(
                    explanation="Fallback topic explanation was used because no LLM key is configured.",
                    suggestions=["Review the topic description in the platform."],
                    next_steps=["Ask for a deeper explanation once AI is enabled."],
                ),
            )
            self.cache.set(cache_key, result.model_dump(mode="json"), ttl=300)
            return result

        data = await self.llm.generate_json(
            system_prompt="You explain topics simply and accurately for learners.",
            user_prompt=explain_topic_prompt(context),
        )
        result = TopicExplainResponse(
            topic_name=payload.topic_name,
            explanation=str(data.get("explanation") or ""),
            examples=[str(item) for item in data.get("examples", [])][:4],
            use_cases=[str(item) for item in data.get("use_cases", [])][:4],
            guidance=self._guidance(data),
        )
        self.cache.set(cache_key, result.model_dump(mode="json"), ttl=self.settings.ai_cache_ttl_seconds)
        return result

    async def generate_questions(self, payload: QuestionGenerationRequest) -> QuestionGenerationResponse:
        context = self._safe_context(payload.model_dump())
        cache_key = self.cache.make_key("generate_questions", context)
        cached = self.cache.get(cache_key)
        if cached:
            return QuestionGenerationResponse(**cached)

        if not self.llm.enabled:
            result = QuestionGenerationResponse(
                topic=payload.topic,
                difficulty=payload.difficulty,
                questions=[],
                guidance=PromptSection(
                    explanation="Fallback mode cannot generate dynamic questions without an LLM key.",
                    suggestions=["Use existing topic questions for now."],
                    next_steps=["Enable AI question generation to create new practice items."],
                ),
            )
            self.cache.set(cache_key, result.model_dump(mode="json"), ttl=120)
            return result

        data = await self.llm.generate_json(
            system_prompt="You generate safe, accurate practice questions for a learning platform.",
            user_prompt=generate_questions_prompt(context),
            max_output_tokens=1400,
        )
        result = QuestionGenerationResponse(
            topic=payload.topic,
            difficulty=payload.difficulty,
            questions=data.get("questions", [])[: payload.count],
            guidance=self._guidance(data),
        )
        self.cache.set(cache_key, result.model_dump(mode="json"), ttl=self.settings.ai_cache_ttl_seconds)
        return result
