from __future__ import annotations

from statistics import mean


class CognitiveModelingService:
    def build_model(
        self,
        *,
        topic_scores: dict[int, float],
        response_times: list[float],
        accuracies: list[float],
        learning_profile: dict,
        past_mistakes: list[str] | None = None,
    ) -> dict:
        past_mistakes = past_mistakes or []
        profile_type = str(learning_profile.get("profile_type", "balanced"))
        avg_response_time = mean(response_times) if response_times else 24.0
        avg_accuracy = mean(accuracies) if accuracies else float(learning_profile.get("accuracy", 50.0) or 50.0)
        weak_topics = [topic_id for topic_id, score in topic_scores.items() if float(score) < 70.0]
        severe_topics = [topic_id for topic_id, score in topic_scores.items() if float(score) < 55.0]

        confusion_signals: list[str] = []
        misunderstanding_patterns: list[str] = []

        if severe_topics:
            confusion_signals.append("Multiple low-scoring topics suggest conceptual confusion, not just missed practice.")
        if avg_response_time > 42:
            confusion_signals.append("Long response times indicate hesitation before committing to answers.")
        if avg_accuracy < 62:
            confusion_signals.append("Accuracy is low enough that the learner likely misunderstands key foundations.")
        if past_mistakes:
            misunderstanding_patterns.append("Repeated mentor-memory mistakes show that some misconceptions persist across sessions.")
        if len(weak_topics) >= 3:
            misunderstanding_patterns.append("Weaknesses spread across several topics suggest prerequisite gaps are compounding.")
        if profile_type == "fast_explorer" and avg_accuracy < 68:
            misunderstanding_patterns.append("The learner moves quickly, but correctness drops when depth is required.")
        if profile_type == "slow_deep_learner" and avg_response_time > 45:
            misunderstanding_patterns.append("The learner thinks carefully, but may be over-processing instead of simplifying the concept.")
        if profile_type == "practice_focused":
            misunderstanding_patterns.append("This learner improves through worked examples and immediate feedback loops.")
        elif profile_type == "concept_focused":
            misunderstanding_patterns.append("This learner responds better when ideas are reframed with intuition before practice.")

        confusion_level = "low"
        if len(severe_topics) >= 2 or (avg_accuracy < 60 and avg_response_time > 38):
            confusion_level = "high"
        elif weak_topics or avg_accuracy < 72:
            confusion_level = "medium"

        if profile_type == "concept_focused":
            teaching_style = "Start with intuition, mental models, and one clean analogy before practice."
        elif profile_type == "practice_focused":
            teaching_style = "Use worked examples first, then quick drills with instant error correction."
        elif profile_type == "slow_deep_learner":
            teaching_style = "Slow down, reduce context switching, and teach one concept chunk at a time."
        elif profile_type == "fast_explorer":
            teaching_style = "Keep the pace high, but force brief comprehension checks before moving on."
        else:
            teaching_style = "Blend concept explanation with one small practical exercise after each idea."

        adaptive_actions = []
        if confusion_level == "high":
            adaptive_actions.append("Reduce difficulty and revisit prerequisites before introducing new material.")
        if weak_topics:
            adaptive_actions.append("Anchor the next session around the single weakest topic to avoid scattered effort.")
        if past_mistakes:
            adaptive_actions.append("Explicitly revisit earlier mistakes so the learner can compare the old and corrected model.")
        adaptive_actions.append("End each explanation with a short comprehension check.")

        return {
            "confusion_level": confusion_level,
            "confusion_signals": confusion_signals[:3],
            "misunderstanding_patterns": misunderstanding_patterns[:4],
            "teaching_style": teaching_style,
            "adaptive_actions": adaptive_actions[:4],
        }
