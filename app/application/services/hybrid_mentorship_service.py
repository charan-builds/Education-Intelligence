from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ai_context_builder import AIContextBuilder
from app.application.services.mentor_service import MentorService
from app.domain.models.user import UserRole
from app.infrastructure.repositories.community_repository import CommunityRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.infrastructure.repositories.user_repository import UserRepository


class HybridMentorshipService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repository = UserRepository(session)
        self.topic_repository = TopicRepository(session)
        self.community_repository = CommunityRepository(session)
        self.mentor_service = MentorService(session=session)
        self.ai_context_builder = AIContextBuilder(session)

    @staticmethod
    def _session_intensity(completion_rate: float, weak_topic_count: int, overdue_steps: int) -> str:
        if completion_rate < 35 or overdue_steps > 2 or weak_topic_count >= 4:
            return "high_touch"
        if completion_rate < 65 or weak_topic_count >= 2:
            return "blended"
        return "light_guidance"

    @staticmethod
    def _availability_label(user_id: int, role: str) -> str:
        if role == "mentor":
            return "Available now" if user_id % 2 == 0 else "Available this afternoon"
        return "Office hours this week"

    @staticmethod
    def _specialties_for_role(role: str, weak_topic_names: list[str], profile_type: str) -> list[str]:
        defaults = ["Roadmap triage", "Revision planning", "Accountability coaching"]
        if role == "teacher":
            defaults = ["Concept explanation", "Assessment review", "Milestone planning"]
        if weak_topic_names:
            return [weak_topic_names[0], *defaults][:3]
        if profile_type == "practice_focused":
            return ["Mock practice", "Error analysis", "Timed drills"]
        if profile_type == "concept_focused":
            return ["Concept breakdown", "Mental models", "Foundation repair"]
        return defaults

    def _mentor_match_score(
        self,
        *,
        mentor_role: str,
        weak_topic_count: int,
        completion_rate: float,
        learning_style: str,
        mentor_id: int,
    ) -> tuple[int, list[str]]:
        base = 72 if mentor_role == "mentor" else 68
        score = base
        reasons: list[str] = []

        if weak_topic_count >= 3:
            score += 10
            reasons.append("Multiple weak topics suggest a human mentor should reinforce the AI study plan.")
        if completion_rate < 55:
            score += 8
            reasons.append("Roadmap momentum is slipping, so accountability and pacing support will help.")
        if learning_style == "practice_focused":
            score += 6
            reasons.append("Practice-heavy learners benefit from live feedback on mistakes and drill strategy.")
        elif learning_style == "concept_focused":
            score += 6
            reasons.append("Concept-heavy learners benefit from a mentor who can reframe ideas in real time.")

        score += min(mentor_id % 7, 4)
        return min(score, 98), reasons[:3]

    async def _topic_name_map(self, tenant_id: int, topic_ids: list[int]) -> dict[int, str]:
        topics = await self.topic_repository.list_topics_by_ids(topic_ids, tenant_id=tenant_id) if topic_ids else []
        return {
            int(topic.id): str(topic.name)
            for topic in topics
            if int(topic.tenant_id) == tenant_id
        }

    async def get_overview(
        self,
        *,
        user_id: int,
        tenant_id: int,
    ) -> dict[str, Any]:
        context = await self.mentor_service._load_user_context(user_id=user_id, tenant_id=tenant_id)
        if context is None:
            return {
                "learner_profile": {
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "completion_rate": 0.0,
                    "learning_style": "balanced",
                    "session_intensity": "blended",
                    "weak_topics": [],
                    "strong_topics": [],
                    "human_support_needed": True,
                    "summary": "Learner context is limited, so the hybrid system is defaulting to guided human support.",
                },
                "mentor_matches": [],
                "collaboration_brief": {
                    "session_goal": "Rebuild learner context and establish the next study milestone.",
                    "ai_role": "Summarize current platform data and propose a first-step plan.",
                    "human_role": "Validate goals, clarify blockers, and turn the plan into accountability.",
                    "shared_context": [],
                    "handoff_notes": [],
                    "escalation_triggers": ["Missing roadmap data", "No recent activity", "Learner reports confusion"],
                },
                "live_support_channels": [
                    {
                        "channel_type": "ai_chat",
                        "title": "AI mentor chat",
                        "description": "Immediate AI support while human mentor context is still limited.",
                        "href": "/mentor/chat",
                        "realtime_enabled": True,
                        "why": "Fastest recovery path while the system rebuilds learner context.",
                    }
                ],
            }

        weak_topics = context.missing_foundations or sorted(
            topic_id for topic_id, score in context.topic_scores.items() if float(score) < 70.0
        )
        strong_topics = [
            int(topic_id)
            for topic_id, score in sorted(context.topic_scores.items(), key=lambda item: item[1], reverse=True)[:5]
            if float(score) >= 75.0
        ]
        topic_names = await self._topic_name_map(tenant_id, [*weak_topics[:5], *strong_topics[:5]])
        weak_topic_names = [topic_names.get(topic_id, f"Topic {topic_id}") for topic_id in weak_topics[:5]]
        strong_topic_names = [topic_names.get(topic_id, f"Topic {topic_id}") for topic_id in strong_topics[:5]]
        profile_type = str(context.learning_profile.get("profile_type", "balanced"))

        mentor_context = await self.ai_context_builder.build_mentor_context(
            user_id=user_id,
            tenant_id=tenant_id,
            learning_profile=context.learning_profile,
            roadmap_progress={
                "completion_rate": context.completion_rate,
                "completed_steps": context.completed_steps,
                "total_steps": len(context.steps),
                "overdue_steps": context.overdue_steps,
            },
            weak_topics=weak_topics[:5],
            topic_scores=context.topic_scores,
            cognitive_model=context.cognitive_model,
        )
        memory_profile = mentor_context.get("memory_profile", {})

        mentors = await self.user_repository.list_by_tenant_and_roles(
            tenant_id,
            roles=[UserRole.mentor, UserRole.teacher],
            limit=8,
        )
        mentor_matches: list[dict[str, Any]] = []
        for mentor in mentors:
            if int(mentor.id) == user_id:
                continue
            score, reasons = self._mentor_match_score(
                mentor_role=mentor.role.value,
                weak_topic_count=len(weak_topics),
                completion_rate=context.completion_rate,
                learning_style=profile_type,
                mentor_id=int(mentor.id),
            )
            mentor_matches.append(
                {
                    "mentor_id": int(mentor.id),
                    "display_name": mentor.display_name or mentor.email.split("@")[0].replace(".", " ").title(),
                    "email": mentor.email,
                    "role": mentor.role.value,
                    "match_score": score,
                    "availability": self._availability_label(int(mentor.id), mentor.role.value),
                    "specialties": self._specialties_for_role(mentor.role.value, weak_topic_names, profile_type),
                    "reasons": reasons or ["This mentor can translate AI guidance into a concrete weekly plan."],
                    "ai_handoff_summary": (
                        f"AI would brief this mentor on {', '.join(weak_topic_names[:2]) or 'current weak areas'} "
                        f"and the learner's {profile_type} pattern before the live session."
                    ),
                }
            )
        mentor_matches.sort(key=lambda item: item["match_score"], reverse=True)

        communities = await self.community_repository.list_communities(tenant_id=tenant_id, limit=50, offset=0)
        topic_community = next((community for community in communities if int(community.topic_id) in set(weak_topics[:3])), None)

        handoff_notes = [
            f"Primary weak topics: {', '.join(weak_topic_names) if weak_topic_names else 'none detected'}.",
            f"Strong topics to leverage for confidence: {', '.join(strong_topic_names) if strong_topic_names else 'still emerging'}.",
            f"Learning style: {profile_type}.",
            f"Recent memory signal: {memory_profile.get('last_session_summary') or 'No prior mentor summary stored.'}",
        ]
        shared_context = [
            f"Roadmap completion is {context.completion_rate:.1f}% with {context.overdue_steps} overdue step(s).",
            f"Completed roadmap steps: {context.completed_steps}/{len(context.steps)}.",
            f"Preferred learning style: {mentor_context.get('user_profile', {}).get('preferred_learning_style') or profile_type}.",
            f"Learning speed signal: {mentor_context.get('user_profile', {}).get('learning_speed', 0)} minutes per recent session.",
        ]

        return {
            "learner_profile": {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "completion_rate": round(context.completion_rate, 2),
                "learning_style": profile_type,
                "session_intensity": self._session_intensity(context.completion_rate, len(weak_topics), context.overdue_steps),
                "weak_topics": weak_topic_names,
                "strong_topics": strong_topic_names,
                "human_support_needed": bool(len(weak_topics) >= 2 or context.overdue_steps > 0 or context.completion_rate < 65),
                "summary": (
                    f"The hybrid mentor system sees a {profile_type} learner with {len(weak_topics)} weak topic signal(s), "
                    f"{context.completion_rate:.1f}% roadmap completion, and a need for blended AI + human guidance."
                ),
            },
            "mentor_matches": mentor_matches[:4],
            "collaboration_brief": {
                "session_goal": (
                    f"Stabilize progress on {weak_topic_names[0] if weak_topic_names else 'the next roadmap milestone'} "
                    "and convert AI recommendations into a human-validated weekly plan."
                ),
                "ai_role": "Monitor performance signals, produce a concise learner brief, and suggest next-best interventions.",
                "human_role": "Refine the plan, coach through confusion, and apply judgment where the learner needs empathy or accountability.",
                "shared_context": shared_context,
                "handoff_notes": handoff_notes,
                "escalation_triggers": [
                    "Two or more overdue roadmap steps",
                    "Repeated mistakes across the same weak topic",
                    "Falling focus score or missed review sessions",
                ],
            },
            "live_support_channels": [
                {
                    "channel_type": "ai_chat",
                    "title": "AI mentor chat",
                    "description": "Immediate guidance with memory-backed context and streamed responses.",
                    "href": "/mentor/chat",
                    "realtime_enabled": True,
                    "why": "Best for instant clarification before or after a human mentor session.",
                },
                {
                    "channel_type": "mentor_session",
                    "title": "Live mentor session",
                    "description": "Book a focused human session with AI-generated briefing notes and follow-up actions.",
                    "href": "/mentor/network",
                    "realtime_enabled": True,
                    "why": "Best for nuanced coaching, accountability, and adapting strategy live.",
                },
                {
                    "channel_type": "community",
                    "title": topic_community.name if topic_community is not None else "Community discussion",
                    "description": (
                        f"Topic-aligned peer discussion around {topic_names.get(int(topic_community.topic_id), 'current weak topics')}."
                        if topic_community is not None
                        else "Join a live discussion thread when peer reinforcement will help."
                    ),
                    "href": "/community",
                    "realtime_enabled": True,
                    "why": "Best for quick follow-up questions and social momentum between mentor sessions.",
                },
            ],
        }

    async def build_session_plan(
        self,
        *,
        user_id: int,
        tenant_id: int,
        mentor_id: int | None = None,
        topic_id: int | None = None,
    ) -> dict[str, Any]:
        overview = await self.get_overview(user_id=user_id, tenant_id=tenant_id)
        matches = overview.get("mentor_matches", [])
        selected = next((item for item in matches if item["mentor_id"] == mentor_id), None) if mentor_id is not None else None
        if selected is None:
            selected = matches[0] if matches else None

        weak_topics = list(overview["learner_profile"].get("weak_topics", []))
        chosen_topic = None
        if topic_id is not None:
            chosen_topic = f"Topic {topic_id}"
        elif weak_topics:
            chosen_topic = weak_topics[0]
        else:
            chosen_topic = "Next roadmap milestone"

        mentor_name = selected["display_name"] if selected is not None else "Hybrid mentor"
        return {
            "mentor_id": selected["mentor_id"] if selected is not None else None,
            "mentor_name": mentor_name,
            "session_title": f"{chosen_topic} recovery and momentum session",
            "agenda": [
                "Review the AI-generated learner brief and current roadmap risks.",
                f"Diagnose confusion around {chosen_topic} with targeted examples.",
                "Agree on one revision task, one practice task, and one checkpoint.",
                "Set the next AI follow-up so the system can monitor execution.",
            ],
            "ai_prep_notes": [
                *overview["collaboration_brief"]["shared_context"][:3],
                *overview["collaboration_brief"]["handoff_notes"][:2],
            ],
            "mentor_focus": (
                selected["specialties"]
                if selected is not None
                else ["Roadmap triage", "Confidence rebuilding", "Accountability"]
            ),
            "follow_up_actions": [
                "AI mentor sends a next-day check-in prompt.",
                "Human mentor reviews progress after the next study block.",
                "Escalate to a new session if the same topic remains weak after one revision cycle.",
            ],
        }
