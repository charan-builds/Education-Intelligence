from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ai_context_builder import AIContextBuilder
from app.core.feature_flags import FeatureFlagService
from app.domain.engines.knowledge_graph import KnowledgeGraphEngine
from app.domain.engines.learning_profile_engine import LearningProfileEngine
from app.domain.models.diagnostic_test import DiagnosticTest
from app.domain.models.mentor_suggestion import MentorSuggestion
from app.domain.models.user import User
from app.infrastructure.clients.ai_service_client import AIServiceClient
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.repositories.topic_repository import TopicRepository


@dataclass(frozen=True)
class MentorAdvice:
    summary: str
    recommendations: list[str]
    risk_level: str


@dataclass(frozen=True)
class LearnerMentorContext:
    tenant_id: int
    steps: list
    completed_steps: int
    completion_rate: float
    overdue_steps: int
    topic_scores: dict[int, float]
    learning_profile: dict[str, str | float]
    missing_foundations: list[int]


class MentorAdvisor(Protocol):
    def generate_advice(
        self,
        diagnostic_results: dict[int, float],
        roadmap_progress: dict,
        learning_profile: dict,
    ) -> MentorAdvice: ...


class RuleBasedMentorAdvisor:
    """
    Deterministic baseline mentor logic.
    Replaceable by an LLM-backed advisor later.
    """

    def generate_advice(
        self,
        diagnostic_results: dict[int, float],
        roadmap_progress: dict,
        learning_profile: dict,
    ) -> MentorAdvice:
        weak_topics = [topic_id for topic_id, score in diagnostic_results.items() if score < 60]
        completion_rate = float(roadmap_progress.get("completion_rate", 0.0))
        overdue_steps = int(roadmap_progress.get("overdue_steps", 0))
        profile_type = str(learning_profile.get("profile_type", "balanced"))

        recommendations: list[str] = []
        if weak_topics:
            recommendations.append(
                f"Revisit weak topics first: {', '.join(map(str, sorted(weak_topics)))}."
            )
        else:
            recommendations.append("Maintain momentum by practicing mixed difficulty problems.")

        if completion_rate < 40:
            recommendations.append("Break roadmap steps into smaller daily targets to improve consistency.")
        elif completion_rate > 75:
            recommendations.append("You can accelerate to the next milestone while keeping revision sessions.")

        if overdue_steps > 0:
            recommendations.append("Resolve overdue roadmap items before taking on new advanced topics.")

        if profile_type == "slow_deep_learner":
            recommendations.append("Use long-form concept sessions and fewer context switches each day.")
        elif profile_type == "practice_focused":
            recommendations.append("Add timed drills and immediate error review after each session.")
        elif profile_type == "concept_focused":
            recommendations.append("Pair conceptual learning with one practical task per topic.")

        risk_level = "low"
        if completion_rate < 30 or (weak_topics and overdue_steps > 0):
            risk_level = "high"
        elif completion_rate < 60 or weak_topics:
            risk_level = "medium"

        summary = (
            f"Profile: {profile_type}; completion: {completion_rate:.1f}%; "
            f"weak_topics: {len(weak_topics)}; overdue_steps: {overdue_steps}."
        )

        return MentorAdvice(summary=summary, recommendations=recommendations, risk_level=risk_level)


class MentorService:
    def __init__(self, advisor: MentorAdvisor | None = None, session: AsyncSession | None = None):
        self.advisor = advisor or RuleBasedMentorAdvisor()
        self._fallback_advisor = RuleBasedMentorAdvisor()
        self.session = session

        self.diagnostic_repository = DiagnosticRepository(session) if session is not None else None
        self.roadmap_repository = RoadmapRepository(session) if session is not None else None
        self.topic_repository = TopicRepository(session) if session is not None else None
        self.learning_profile_engine = LearningProfileEngine()
        self.ai_service_client = AIServiceClient()
        self.feature_flag_service = FeatureFlagService(session) if session is not None else None
        self.ai_context_builder = AIContextBuilder(session) if session is not None else None

    def get_personalized_advice(
        self,
        diagnostic_results: dict[int, float],
        roadmap_progress: dict,
        learning_profile: dict,
        feature_flags: dict[str, bool] | None = None,
    ) -> dict:
        flags = feature_flags or {}
        advisor = self.advisor if flags.get("ai_mentor_enabled", True) else self._fallback_advisor
        advice = advisor.generate_advice(
            diagnostic_results=diagnostic_results,
            roadmap_progress=roadmap_progress,
            learning_profile=learning_profile,
        )
        return {
            "summary": advice.summary,
            "recommendations": advice.recommendations,
            "risk_level": advice.risk_level,
            "advisor_type": advisor.__class__.__name__,
        }

    async def contextual_suggestions(self, *, user_id: int, tenant_id: int) -> dict:
        stored_result = await self.session.execute(
            select(MentorSuggestion)
            .where(MentorSuggestion.user_id == user_id, MentorSuggestion.tenant_id == tenant_id)
            .order_by(MentorSuggestion.created_at.desc())
            .limit(4)
        )
        stored = stored_result.scalars().all()
        if stored:
            return {
                "suggestions": [item.message for item in stored],
                "reasons": [item.why_reason for item in stored],
            }

        guidance_text = await self.generate_advice(
            user_id=user_id,
            message="Provide concise next-step suggestions with rationale.",
        )
        chunks = [chunk.strip() for chunk in guidance_text.split(".") if chunk.strip()]
        return {
            "suggestions": chunks[:4] or ["Complete one pending roadmap step today."],
            "reasons": ["Generated from your roadmap progress, weak-topic profile, and current momentum."],
        }

    async def _load_user_context(
        self,
        *,
        user_id: int,
        tenant_id: int | None = None,
    ) -> LearnerMentorContext | None:
        if self.session is None or self.diagnostic_repository is None or self.roadmap_repository is None or self.topic_repository is None:
            return None

        user_stmt = select(User).where(User.id == user_id)
        if tenant_id is not None:
            user_stmt = user_stmt.where(User.tenant_id == tenant_id)

        user_row = await self.session.execute(user_stmt)
        user = user_row.scalar_one_or_none()
        if user is None:
            return None

        effective_tenant_id = int(user.tenant_id)

        roadmap_items = await self.roadmap_repository.list_user_roadmaps(
            user_id=user_id,
            tenant_id=effective_tenant_id,
            limit=1,
            offset=0,
        )
        latest_roadmap = roadmap_items[0] if roadmap_items else None
        steps = latest_roadmap.steps if latest_roadmap else []

        completed_steps = sum(1 for step in steps if str(step.progress_status).lower() == "completed")
        completion_rate = (completed_steps / len(steps) * 100.0) if steps else 0.0
        overdue_steps = sum(
            1
            for step in steps
            if str(step.progress_status).lower() != "completed" and getattr(step, "deadline", None) is not None
        )

        latest_test_row = await self.session.execute(
            select(DiagnosticTest)
            .where(DiagnosticTest.user_id == user_id)
            .order_by(DiagnosticTest.id.desc())
            .limit(1)
        )
        latest_test = latest_test_row.scalar_one_or_none()

        topic_scores: dict[int, float] = {}
        learning_profile: dict[str, str | float] = {"profile_type": "balanced", "confidence": 0.5}
        missing_foundations: list[int] = []

        if latest_test is not None:
            topic_scores = await self.diagnostic_repository.topic_scores_for_test(
                test_id=latest_test.id,
                user_id=user_id,
                tenant_id=effective_tenant_id,
            )
            analytics = await self.diagnostic_repository.answer_analytics_for_test(
                test_id=latest_test.id,
                user_id=user_id,
                tenant_id=effective_tenant_id,
            )
            profile = self.learning_profile_engine.analyze(
                response_times=analytics.get("response_times", []),
                accuracies=analytics.get("accuracies", []),
                difficulty_distribution=analytics.get("difficulty_distribution", {}),
            )
            learning_profile = {"profile_type": profile.profile_type, "confidence": profile.confidence}

            knowledge_graph = KnowledgeGraphEngine(self.topic_repository)
            missing_foundations = await knowledge_graph.detect_missing_foundations(
                topic_scores=topic_scores,
                tenant_id=effective_tenant_id,
            )

        return LearnerMentorContext(
            tenant_id=effective_tenant_id,
            steps=steps,
            completed_steps=completed_steps,
            completion_rate=completion_rate,
            overdue_steps=overdue_steps,
            topic_scores=topic_scores,
            learning_profile=learning_profile,
            missing_foundations=missing_foundations,
        )

    async def generate_advice(self, user_id: int, message: str) -> str:
        if self.session is None or self.diagnostic_repository is None or self.roadmap_repository is None or self.topic_repository is None:
            normalized = message.strip()
            if not normalized:
                return "Please share your learning question so I can help."
            return (
                "Focus on one weak topic, complete one roadmap step today, and summarize a key concept. "
                f"You asked: '{normalized[:240]}'"
            )

        context = await self._load_user_context(user_id=user_id)
        if context is None:
            return "User context not found. Please login again and retry."

        advice = self.get_personalized_advice(
            diagnostic_results=context.topic_scores,
            roadmap_progress={"completion_rate": context.completion_rate, "overdue_steps": context.overdue_steps},
            learning_profile=context.learning_profile,
        )

        guidance = [
            f"{advice['summary']}",
            f"Learning profile: {context.learning_profile['profile_type']}.",
            f"Roadmap completion: {context.completion_rate:.1f}% ({context.completed_steps}/{len(context.steps)} steps).",
            f"Weak foundations detected: {len(context.missing_foundations)} topic(s).",
            f"Guidance: {' '.join(advice['recommendations'])}",
        ]

        ai_enabled = False
        if self.feature_flag_service is not None:
            ai_enabled = await self.feature_flag_service.is_enabled("ai_mentor_enabled", context.tenant_id)
        if ai_enabled:
            weak_topics = context.missing_foundations or sorted(
                topic_id for topic_id, score in context.topic_scores.items() if score < 70.0
            )
            mentor_context = (
                await self.ai_context_builder.build_mentor_context(
                    user_id=user_id,
                    tenant_id=context.tenant_id,
                    learning_profile=context.learning_profile,
                    roadmap_progress={
                        "completion_rate": context.completion_rate,
                        "completed_steps": context.completed_steps,
                        "total_steps": len(context.steps),
                        "overdue_steps": context.overdue_steps,
                    },
                    weak_topics=weak_topics,
                    topic_scores=context.topic_scores,
                )
                if self.ai_context_builder is not None
                else None
            )
            ai_reply = await self._try_ai_mentor_response(
                user_id=user_id,
                tenant_id=context.tenant_id,
                goal=None,
                message=message,
                steps=context.steps,
                weak_topics=weak_topics,
                learning_profile=context.learning_profile,
                mentor_context=mentor_context,
                chat_history=[],
            )
            if ai_reply and ai_reply.get("reply"):
                guidance.append(f"AI mentor: {ai_reply['reply']}")

        if message.strip():
            guidance.append(f"Regarding your message: '{message.strip()[:240]}'")
        return " ".join(guidance)

    async def _try_ai_mentor_response(
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
    ) -> dict | None:
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
                return None
            return {
                "reply": str(response),
                "suggested_focus_topics": [
                    int(topic_id)
                    for topic_id in result.get("suggested_focus_topics", [])
                    if str(topic_id).isdigit()
                ],
                "why_recommended": [str(item) for item in (result.get("guidance") or {}).get("suggestions", [])][:3],
                "provider": result.get("provider"),
                "next_checkin_date": result.get("next_checkin_date"),
                "session_summary": str(result.get("session_summary") or ""),
                "memory_update": result.get("memory_update") if isinstance(result.get("memory_update"), dict) else {},
            }
        except Exception:
            return None

    async def progress_analysis(self, user_id: int) -> dict:
        if self.session is None or self.diagnostic_repository is None or self.roadmap_repository is None or self.topic_repository is None:
            return {
                "topic_improvements": {},
                "weekly_progress": [
                    {"week": "W1", "completion_percent": 0.0},
                    {"week": "W2", "completion_percent": 0.0},
                    {"week": "W3", "completion_percent": 0.0},
                    {"week": "W4", "completion_percent": 0.0},
                ],
                "recommended_focus": [
                    "Start with one pending roadmap topic.",
                    "Practice weak foundations for 30 minutes daily.",
                ],
            }

        user_row = await self.session.execute(select(User).where(User.id == user_id))
        user = user_row.scalar_one_or_none()
        if user is None:
            return {
                "topic_improvements": {},
                "weekly_progress": [],
                "recommended_focus": ["User context not found."],
            }

        tenant_id = int(user.tenant_id)

        latest_test_row = await self.session.execute(
            select(DiagnosticTest)
            .where(DiagnosticTest.user_id == user_id)
            .order_by(DiagnosticTest.id.desc())
            .limit(1)
        )
        latest_test = latest_test_row.scalar_one_or_none()

        topic_scores: dict[int, float] = {}
        if latest_test is not None:
            topic_scores = await self.diagnostic_repository.topic_scores_for_test(
                test_id=latest_test.id,
                user_id=user_id,
                tenant_id=tenant_id,
            )

        # Deterministic improvement proxy: distance from mastery threshold.
        topic_improvements = {
            int(topic_id): round(max(0.0, 70.0 - float(score)), 2)
            for topic_id, score in topic_scores.items()
        }

        roadmap_items = await self.roadmap_repository.list_user_roadmaps(
            user_id=user_id,
            tenant_id=tenant_id,
            limit=1,
            offset=0,
        )
        latest_roadmap = roadmap_items[0] if roadmap_items else None
        steps = latest_roadmap.steps if latest_roadmap else []

        total_steps = len(steps)
        completed_steps = sum(1 for step in steps if str(step.progress_status).lower() == "completed")
        current_completion = (completed_steps / total_steps * 100.0) if total_steps else 0.0

        # Simple four-week trend approximation for dashboarding.
        weekly_progress: list[dict[str, float | int | str]] = []
        for week in range(1, 5):
            scale = week / 4
            weekly_progress.append(
                {
                    "week": f"W{week}",
                    "completion_percent": round(current_completion * scale, 2),
                }
            )

        weak_topics = sorted([topic_id for topic_id, score in topic_scores.items() if score < 70.0])
        recommended_focus = []
        if weak_topics:
            recommended_focus.append(
                f"Focus on weak topics first: {', '.join(map(str, weak_topics[:5]))}."
            )
        else:
            recommended_focus.append("Maintain momentum with mixed-difficulty revision.")

        if total_steps and completed_steps < total_steps:
            recommended_focus.append("Complete the next pending roadmap step this week.")
        else:
            recommended_focus.append("Advance to the next specialization milestone.")

        recommended_focus.append("Track weekly progress and adjust study blocks based on completion trend.")

        ai_enabled = False
        if self.feature_flag_service is not None:
            ai_enabled = await self.feature_flag_service.is_enabled("ai_mentor_enabled", tenant_id)
        if ai_enabled:
            try:
                ai_progress = await self.ai_service_client.analyze_progress(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    completion_percent=current_completion,
                    weak_topics=weak_topics[:5],
                )
                ai_summary = ai_progress.get("summary")
                ai_topics = ai_progress.get("recommended_focus_topics")
                ai_guidance = (ai_progress.get("guidance") or {}).get("suggestions", [])
                if isinstance(ai_summary, str) and ai_summary:
                    recommended_focus.insert(0, ai_summary)
                if isinstance(ai_topics, list):
                    recommended_focus.extend(
                        [f"AI focus topic {int(topic_id)}." for topic_id in ai_topics[:3] if str(topic_id).isdigit()]
                    )
                if isinstance(ai_guidance, list):
                    recommended_focus.extend([str(item) for item in ai_guidance[:2]])
            except Exception:
                pass

        return {
            "topic_improvements": topic_improvements,
            "weekly_progress": weekly_progress,
            "recommended_focus": recommended_focus,
        }

    async def chat(
        self,
        message: str,
        user_id: int,
        tenant_id: int,
        chat_history: list[dict[str, str]] | None = None,
    ) -> dict:
        normalized = message.strip()
        if not normalized:
            return {
                "reply": "Please share your learning question so I can help.",
                "advisor_type": self.advisor.__class__.__name__,
                "used_ai": False,
                "suggested_focus_topics": [],
                "why_recommended": ["A specific question lets the mentor tailor advice to your current roadmap and weak topics."],
                "provider": None,
                "next_checkin_date": None,
                "session_summary": "",
                "memory_summary": {},
            }

        context = await self._load_user_context(user_id=user_id, tenant_id=tenant_id)
        if context is None:
            reply = (
                f"Mentor guidance for user {user_id} (tenant {tenant_id}): "
                "focus next on one weak topic, do 30 minutes of practice, and summarize one key takeaway. "
                f"Your message: '{normalized[:240]}'"
            )
            return {
                "reply": reply,
                "advisor_type": self.advisor.__class__.__name__,
                "used_ai": False,
                "suggested_focus_topics": [],
                "why_recommended": ["Fallback advice was used because learner context could not be loaded."],
                "provider": None,
                "next_checkin_date": None,
                "session_summary": "",
                "memory_summary": {},
            }

        ai_enabled = False
        if self.feature_flag_service is not None:
            ai_enabled = await self.feature_flag_service.is_enabled("ai_mentor_enabled", context.tenant_id)
        if ai_enabled:
            weak_topics = context.missing_foundations or sorted(
                topic_id for topic_id, score in context.topic_scores.items() if score < 70.0
            )
            mentor_context = (
                await self.ai_context_builder.build_mentor_context(
                    user_id=user_id,
                    tenant_id=context.tenant_id,
                    learning_profile=context.learning_profile,
                    roadmap_progress={
                        "completion_rate": context.completion_rate,
                        "completed_steps": context.completed_steps,
                        "total_steps": len(context.steps),
                        "overdue_steps": context.overdue_steps,
                    },
                    weak_topics=weak_topics,
                    topic_scores=context.topic_scores,
                )
                if self.ai_context_builder is not None
                else None
            )
            ai_reply = await self._try_ai_mentor_response(
                user_id=user_id,
                tenant_id=context.tenant_id,
                goal=None,
                message=normalized,
                steps=context.steps,
                weak_topics=weak_topics,
                learning_profile=context.learning_profile,
                mentor_context=mentor_context,
                chat_history=chat_history or [],
            )
            if ai_reply is not None:
                memory_summary = {}
                if self.ai_context_builder is not None:
                    updated_snapshot = await self.ai_context_builder.memory_service.update_after_session(
                        tenant_id=context.tenant_id,
                        user_id=user_id,
                        user_message=normalized,
                        mentor_reply=ai_reply["reply"],
                        memory_update=ai_reply.get("memory_update"),
                    )
                    memory_summary = {
                        "learner_summary": updated_snapshot.learner_summary,
                        "preferred_learning_style": updated_snapshot.preferred_learning_style,
                        "learning_speed": updated_snapshot.learning_speed,
                        "weak_topics_history": updated_snapshot.weak_topics,
                        "strong_topics_history": updated_snapshot.strong_topics,
                        "past_mistakes": updated_snapshot.past_mistakes,
                        "improvement_signals": updated_snapshot.improvement_signals,
                    }
                return {
                    "reply": ai_reply["reply"],
                    "advisor_type": "AIServiceClient",
                    "used_ai": True,
                    "suggested_focus_topics": ai_reply.get("suggested_focus_topics", []),
                    "why_recommended": ai_reply.get("why_recommended", []),
                    "provider": ai_reply.get("provider"),
                    "next_checkin_date": ai_reply.get("next_checkin_date"),
                    "session_summary": ai_reply.get("session_summary", ""),
                    "memory_summary": memory_summary,
                }

        advice = self.get_personalized_advice(
            diagnostic_results=context.topic_scores,
            roadmap_progress={"completion_rate": context.completion_rate, "overdue_steps": context.overdue_steps},
            learning_profile=context.learning_profile,
        )
        weak_topics = context.missing_foundations or sorted(
            topic_id for topic_id, score in context.topic_scores.items() if score < 70.0
        )
        weak_topic_summary = ", ".join(map(str, weak_topics[:5])) if weak_topics else "none identified"
        reply = " ".join(
            [
                str(advice["summary"]),
                f"Focus topics: {weak_topic_summary}.",
                (
                    f"Roadmap completion is {context.completion_rate:.1f}% "
                    f"with {context.completed_steps}/{len(context.steps)} steps completed."
                ),
                f"Recommended next actions: {' '.join(advice['recommendations'][:3])}",
                f"You asked: '{normalized[:240]}'",
            ]
        )
        memory_summary = {}
        session_summary = ""
        if self.ai_context_builder is not None:
            updated_snapshot = await self.ai_context_builder.memory_service.update_after_session(
                tenant_id=context.tenant_id,
                user_id=user_id,
                user_message=normalized,
                mentor_reply=reply,
                memory_update={
                    "learner_summary": str(advice["summary"]),
                    "weak_topics": [str(topic_id) for topic_id in weak_topics[:5]],
                    "strong_topics": [
                        str(topic_id)
                        for topic_id, score in sorted(context.topic_scores.items(), key=lambda item: item[1], reverse=True)[:5]
                        if float(score) >= 75.0
                    ],
                    "past_mistakes": [f"Recurring weakness in topic {topic_id}" for topic_id in weak_topics[:3]],
                    "improvement_signals": [f"Completion rate is now {context.completion_rate:.1f}%."],
                    "preferred_learning_style": str(context.learning_profile.get("profile_type", "balanced")),
                    "learning_speed": float(context.learning_profile.get("speed", 0.0) or 0.0),
                    "session_summary": f"Learner asked about '{normalized[:120]}' and received tailored roadmap guidance.",
                },
            )
            memory_summary = {
                "learner_summary": updated_snapshot.learner_summary,
                "preferred_learning_style": updated_snapshot.preferred_learning_style,
                "learning_speed": updated_snapshot.learning_speed,
                "weak_topics_history": updated_snapshot.weak_topics,
                "strong_topics_history": updated_snapshot.strong_topics,
                "past_mistakes": updated_snapshot.past_mistakes,
                "improvement_signals": updated_snapshot.improvement_signals,
            }
            session_summary = updated_snapshot.last_session_summary
        return {
            "reply": reply,
            "advisor_type": str(advice["advisor_type"]),
            "used_ai": False,
            "suggested_focus_topics": weak_topics[:5],
            "why_recommended": [
                "Low-scoring topics and missing foundations were prioritized first.",
                f"Current roadmap completion is {context.completion_rate:.1f}% with {context.overdue_steps} overdue steps.",
            ],
            "provider": None,
            "next_checkin_date": None,
            "session_summary": session_summary,
            "memory_summary": memory_summary,
        }
