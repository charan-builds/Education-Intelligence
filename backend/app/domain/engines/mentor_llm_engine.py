from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MentorContext:
    user_roadmap: dict
    weak_topics: list[int]
    learning_profile: dict


class MentorLLMEngine(Protocol):
    def generate_response(self, context: MentorContext, message: str) -> str: ...


class RuleBasedMentorLLMEngine:
    """
    Placeholder LLM integration engine.

    This deterministic implementation is safe for MVP usage and can be
    replaced by a real model-backed adapter without changing callers.
    """

    def generate_response(self, context: MentorContext, message: str) -> str:
        normalized = message.strip()
        if not normalized:
            return "Please share your learning question so I can help you effectively."

        roadmap_steps = int(context.user_roadmap.get("total_steps", 0))
        completion_rate = float(context.user_roadmap.get("completion_rate", 0.0))
        profile = str(context.learning_profile.get("profile_type", "balanced"))

        if context.weak_topics:
            weak_topic_text = ", ".join(str(topic_id) for topic_id in sorted(context.weak_topics))
            weak_hint = f"Prioritize weak topics: {weak_topic_text}."
        else:
            weak_hint = "No major weak topics detected; maintain consistent revision."

        return (
            f"Mentor guidance ({profile}): roadmap has {roadmap_steps} steps at {completion_rate:.1f}% completion. "
            f"{weak_hint} Based on your message '{normalized[:240]}', complete one focused practice block and one quick recap today."
        )
