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
    def next_difficulty_from_answer(*, current_difficulty: int, is_correct: bool) -> int:
        """Move one level harder after a correct answer, easier after a wrong one."""
        if is_correct:
            return min(AdaptiveTestingEngine.HARD, int(current_difficulty) + 1)
        return max(AdaptiveTestingEngine.EASY, int(current_difficulty) - 1)

    @staticmethod
    def _normalize_question(question: Any) -> AdaptiveQuestion:
        if isinstance(question, AdaptiveQuestion):
            return question
        question_type = getattr(question, "question_type", "short_text")
        difficulty = getattr(question, "difficulty_level", getattr(question, "difficulty", 2))
        return AdaptiveQuestion(
            id=int(getattr(question, "id")),
            topic_id=int(getattr(question, "topic_id")),
            difficulty=int(difficulty),
            question_type=str(question_type.value if hasattr(question_type, "value") else question_type),
            question_text=str(getattr(question, "question_text")),
            answer_options=list(getattr(question, "answer_options", []) or []),
        )

    def _target_difficulty(
        self,
        normalized_questions: list[AdaptiveQuestion],
        previous_answers: list[dict],
        learning_profile: dict[str, Any] | None = None,
    ) -> int:
        learning_profile = learning_profile or {}
        if not previous_answers:
            base_difficulty = self.MEDIUM
            difficulty_preference = str(learning_profile.get("difficulty_preference", "moderate"))
            if difficulty_preference == "guided":
                return self.EASY
            if difficulty_preference == "challenging":
                return self.HARD
            return base_difficulty

        question_by_id = {q.id: q for q in normalized_questions}
        last = previous_answers[-1]
        last_question = question_by_id.get(int(last.get("question_id", 0)))
        base = last_question.difficulty if last_question else self.MEDIUM
        last_score = float(last.get("score", 0.0) or 0.0)
        if "is_correct" in last:
            return self.next_difficulty_from_answer(
                current_difficulty=base,
                is_correct=bool(last.get("is_correct")),
            )
        if "score" in last:
            return self.next_difficulty_from_answer(
                current_difficulty=base,
                is_correct=last_score >= self.CORRECT_THRESHOLD,
            )

        last_accuracy = float(last.get("accuracy", last_score / 100.0))
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
            base = min(self.HARD, base + 1)
        elif len(recent_correct) == 2 and not any(recent_correct):
            base = max(self.EASY, base - 1)

        difficulty_preference = str(learning_profile.get("difficulty_preference", "moderate"))
        learning_speed = float(learning_profile.get("learning_speed", 50.0) or 50.0)
        if difficulty_preference == "guided":
            base = max(self.EASY, base - 1)
        elif difficulty_preference == "challenging":
            base = min(self.HARD, base + 1)
        elif learning_speed >= 75:
            base = min(self.HARD, base + 1)
        elif learning_speed <= 35:
            base = max(self.EASY, base - 1)
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

    @staticmethod
    def _topic_answer_counts(previous_answers: list[dict], question_by_id: dict[int, AdaptiveQuestion]) -> dict[int, int]:
        counts: dict[int, int] = {}
        for answer in previous_answers:
            question = question_by_id.get(int(answer.get("question_id", 0)))
            if question is None:
                continue
            counts[question.topic_id] = counts.get(question.topic_id, 0) + 1
        return counts

    def _balanced_candidates(
        self,
        *,
        remaining: list[AdaptiveQuestion],
        previous_answers: list[dict],
        question_by_id: dict[int, AdaptiveQuestion],
        target_topic: int,
        target_difficulty: int,
    ) -> list[AdaptiveQuestion]:
        topic_counts = self._topic_answer_counts(previous_answers, question_by_id)
        min_topic_count = min((topic_counts.get(question.topic_id, 0) for question in remaining), default=0)
        under_covered_topics = {
            question.topic_id
            for question in remaining
            if topic_counts.get(question.topic_id, 0) == min_topic_count
        }

        exact_balanced = [
            question
            for question in remaining
            if question.topic_id in under_covered_topics and question.difficulty == target_difficulty
        ]
        if exact_balanced:
            return exact_balanced

        in_target_topic = [question for question in remaining if question.topic_id == target_topic]
        if in_target_topic:
            return in_target_topic

        balanced = [question for question in remaining if question.topic_id in under_covered_topics]
        return balanced or remaining

    def select_next_question(
        self,
        questions: list[Any],
        previous_answers: list[dict],
        topic_scores: dict[int, float] | None,
        weakness_topic_ids: list[int] | None = None,
        feature_flags: dict[str, bool] | None = None,
        learning_profile: dict[str, Any] | None = None,
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

        question_by_id = {q.id: q for q in normalized_questions}
        target_difficulty = self._target_difficulty(normalized_questions, previous_answers, learning_profile=learning_profile)
        target_topic = self._target_topic(remaining, previous_answers, topic_scores, weakness_topic_ids=weakness_topic_ids)
        candidates = self._balanced_candidates(
            remaining=remaining,
            previous_answers=previous_answers,
            question_by_id=question_by_id,
            target_topic=target_topic,
            target_difficulty=target_difficulty,
        )

        def sort_key(question: AdaptiveQuestion) -> tuple[int, int, int]:
            topic_penalty = 0 if question.topic_id == target_topic else 1
            return (abs(question.difficulty - target_difficulty), topic_penalty, question.difficulty, question.id)

        if candidates:
            question = sorted(candidates, key=sort_key)[0]
            return AdaptiveSelectionResult(
                question=question,
                target_topic_id=target_topic,
                target_difficulty=target_difficulty,
                strategy="adaptive_balanced",
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
