from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AdaptiveQuestion:
    id: int
    topic_id: int
    difficulty: int
    question_text: str
    question_type: str = "short_text"
    answer_options: list[str] | None = None


@dataclass(frozen=True)
class AdaptiveSelectionResult:
    question: AdaptiveQuestion
    target_topic_id: int
    target_difficulty: int
    strategy: str
    weakness_topic_ids: list[int]

    @property
    def id(self) -> int:
        return self.question.id

    @property
    def topic_id(self) -> int:
        return self.question.topic_id

    @property
    def difficulty(self) -> int:
        return self.question.difficulty

    @property
    def question_text(self) -> str:
        return self.question.question_text

    @property
    def question_type(self) -> str:
        return self.question.question_type

    @property
    def answer_options(self) -> list[str] | None:
        return self.question.answer_options


class AdaptiveTestingEngine:
    EASY = 1
    MEDIUM = 2
    HARD = 3
    MAX_QUESTIONS = 12
    CORRECT_THRESHOLD = 70.0
    FAST_THRESHOLD_SECONDS = 20.0
    SLOW_THRESHOLD_SECONDS = 45.0

    @staticmethod
    def _normalize_question(question: Any) -> AdaptiveQuestion:
        if isinstance(question, AdaptiveQuestion):
            return question
        return AdaptiveQuestion(
            id=int(getattr(question, "id")),
            topic_id=int(getattr(question, "topic_id")),
            difficulty=int(getattr(question, "difficulty")),
            question_type=str(getattr(question, "question_type", "short_text")),
            question_text=str(getattr(question, "question_text")),
            answer_options=list(getattr(question, "answer_options", []) or []),
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
        last_accuracy = float(last.get("accuracy", float(last.get("score", 0.0)) / 100.0))
        last_time_taken = float(last.get("time_taken", 0.0) or 0.0)
        last_attempt_count = int(last.get("attempt_count", 1) or 1)

        if (
            last_accuracy >= 0.85
            and last_time_taken <= self.FAST_THRESHOLD_SECONDS
            and last_attempt_count <= 1
        ):
            return min(self.HARD, base + 1)
        if (
            last_accuracy < 0.5
            and (last_time_taken >= self.SLOW_THRESHOLD_SECONDS or last_attempt_count >= 2)
        ):
            return max(self.EASY, base - 1)

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
        weakness_topic_ids: list[int] | None = None,
    ) -> int:
        available_topics = sorted({q.topic_id for q in normalized_questions})
        if not available_topics:
            raise ValueError("No topics available")

        for topic_id in weakness_topic_ids or []:
            if topic_id in available_topics:
                return topic_id

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
        weakness_topic_ids: list[int] | None = None,
        feature_flags: dict[str, bool] | None = None,
    ) -> AdaptiveSelectionResult | None:
        normalized_questions = [self._normalize_question(question) for question in questions]
        if not normalized_questions:
            return None
        if len(previous_answers) >= self.MAX_QUESTIONS:
            return None

        flags = feature_flags or {}
        if not flags.get("adaptive_testing_enabled", True):
            # Deterministic fixed-mode fallback: medium-first then lowest id.
            remaining = sorted(normalized_questions, key=lambda q: (abs(q.difficulty - self.MEDIUM), q.id))
            answered_ids = {int(answer.get("question_id", 0)) for answer in previous_answers}
            for question in remaining:
                if question.id not in answered_ids:
                    return AdaptiveSelectionResult(
                        question=question,
                        target_topic_id=question.topic_id,
                        target_difficulty=self.MEDIUM,
                        strategy="fixed_fallback",
                        weakness_topic_ids=list(weakness_topic_ids or []),
                    )
            return None

        answered_ids = {int(answer.get("question_id", 0)) for answer in previous_answers}
        remaining = [question for question in normalized_questions if question.id not in answered_ids]
        if not remaining:
            return None

        target_difficulty = self._target_difficulty(normalized_questions, previous_answers)
        target_topic = self._target_topic(remaining, previous_answers, topic_scores, weakness_topic_ids=weakness_topic_ids)

        in_topic = [question for question in remaining if question.topic_id == target_topic]

        def sort_key(question: AdaptiveQuestion) -> tuple[int, int, int]:
            return (abs(question.difficulty - target_difficulty), question.difficulty, question.id)

        if in_topic:
            question = sorted(in_topic, key=sort_key)[0]
            return AdaptiveSelectionResult(
                question=question,
                target_topic_id=target_topic,
                target_difficulty=target_difficulty,
                strategy="adaptive_targeted",
                weakness_topic_ids=list(weakness_topic_ids or []),
            )

        question = sorted(remaining, key=lambda q: (q.topic_id, *sort_key(q)))[0]
        return AdaptiveSelectionResult(
            question=question,
            target_topic_id=target_topic,
            target_difficulty=target_difficulty,
            strategy="adaptive_fallback",
            weakness_topic_ids=list(weakness_topic_ids or []),
        )
