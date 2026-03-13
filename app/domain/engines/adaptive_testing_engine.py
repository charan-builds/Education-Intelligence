from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AdaptiveQuestion:
    id: int
    topic_id: int
    difficulty: int
    question_text: str


class AdaptiveTestingEngine:
    EASY = 1
    MEDIUM = 2
    HARD = 3
    CORRECT_THRESHOLD = 70.0

    @staticmethod
    def _normalize_question(question: Any) -> AdaptiveQuestion:
        if isinstance(question, AdaptiveQuestion):
            return question
        return AdaptiveQuestion(
            id=int(getattr(question, "id")),
            topic_id=int(getattr(question, "topic_id")),
            difficulty=int(getattr(question, "difficulty")),
            question_text=str(getattr(question, "question_text")),
        )

    def _target_difficulty(
        self,
        normalized_questions: list[AdaptiveQuestion],
        previous_answers: list[dict],
    ) -> int:
        if not previous_answers:
            return self.MEDIUM

        question_by_id = {q.id: q for q in normalized_questions}
        last = previous_answers[-1]
        last_question = question_by_id.get(int(last.get("question_id", 0)))
        base = last_question.difficulty if last_question else self.MEDIUM

        recent = previous_answers[-2:]
        recent_correct = [float(answer.get("score", 0.0)) >= self.CORRECT_THRESHOLD for answer in recent]

        if len(recent_correct) == 2 and all(recent_correct):
            return min(self.HARD, base + 1)
        if len(recent_correct) == 2 and not any(recent_correct):
            return max(self.EASY, base - 1)
        return base

    def _target_topic(
        self,
        normalized_questions: list[AdaptiveQuestion],
        previous_answers: list[dict],
        topic_scores: dict[int, float] | None,
    ) -> int:
        available_topics = sorted({q.topic_id for q in normalized_questions})
        if not available_topics:
            raise ValueError("No topics available")

        if topic_scores:
            weakest_score = min(topic_scores.values())
            weakest_topics = sorted(topic_id for topic_id, score in topic_scores.items() if score == weakest_score)
            for topic_id in weakest_topics:
                if topic_id in available_topics:
                    return topic_id

        question_by_id = {q.id: q for q in normalized_questions}
        incorrect_topics: dict[int, int] = {}
        for answer in previous_answers:
            if float(answer.get("score", 0.0)) >= self.CORRECT_THRESHOLD:
                continue
            question = question_by_id.get(int(answer.get("question_id", 0)))
            if question is None:
                continue
            incorrect_topics[question.topic_id] = incorrect_topics.get(question.topic_id, 0) + 1

        if incorrect_topics:
            max_failures = max(incorrect_topics.values())
            return sorted(topic for topic, count in incorrect_topics.items() if count == max_failures)[0]

        return available_topics[0]

    def select_next_question(
        self,
        questions: list[Any],
        previous_answers: list[dict],
        topic_scores: dict[int, float] | None,
        feature_flags: dict[str, bool] | None = None,
    ) -> AdaptiveQuestion | None:
        normalized_questions = [self._normalize_question(question) for question in questions]
        if not normalized_questions:
            return None

        flags = feature_flags or {}
        if not flags.get("adaptive_testing_enabled", True):
            # Deterministic fixed-mode fallback: medium-first then lowest id.
            remaining = sorted(normalized_questions, key=lambda q: (abs(q.difficulty - self.MEDIUM), q.id))
            answered_ids = {int(answer.get("question_id", 0)) for answer in previous_answers}
            for question in remaining:
                if question.id not in answered_ids:
                    return question
            return None

        answered_ids = {int(answer.get("question_id", 0)) for answer in previous_answers}
        remaining = [question for question in normalized_questions if question.id not in answered_ids]
        if not remaining:
            return None

        target_difficulty = self._target_difficulty(normalized_questions, previous_answers)
        target_topic = self._target_topic(remaining, previous_answers, topic_scores)

        in_topic = [question for question in remaining if question.topic_id == target_topic]

        def sort_key(question: AdaptiveQuestion) -> tuple[int, int, int]:
            return (abs(question.difficulty - target_difficulty), question.difficulty, question.id)

        if in_topic:
            return sorted(in_topic, key=sort_key)[0]

        return sorted(remaining, key=lambda q: (q.topic_id, *sort_key(q)))[0]
