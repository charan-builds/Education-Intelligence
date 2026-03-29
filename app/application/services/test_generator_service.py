from __future__ import annotations

from collections import defaultdict

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import ValidationError
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.goal_repository import GoalRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.infrastructure.repositories.topic_score_repository import TopicScoreRepository


class SmartTestGeneratorService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.topic_repository = TopicRepository(session)
        self.diagnostic_repository = DiagnosticRepository(session)
        self.goal_repository = GoalRepository(session)
        self.topic_score_repository = TopicScoreRepository(session)

    @staticmethod
    def _difficulty_label(difficulty: int) -> str:
        return {1: "easy", 2: "medium", 3: "hard"}.get(int(difficulty), "medium")

    @staticmethod
    def _target_difficulty(*, mastery_score: float, confidence: float) -> int:
        if mastery_score < 40.0:
            base = 1
        elif mastery_score < 72.0:
            base = 2
        else:
            base = 3

        if confidence < 0.45:
            base = max(1, base - 1)
        elif confidence >= 0.8 and mastery_score >= 78.0:
            base = min(3, base + 1)
        return base

    @staticmethod
    def _difficulty_preference(target_difficulty: int) -> list[int]:
        if int(target_difficulty) <= 1:
            return [1, 2, 3]
        if int(target_difficulty) >= 3:
            return [3, 2, 1]
        return [2, 1, 3]

    async def generate_smart_test(
        self,
        *,
        tenant_id: int,
        user_id: int,
        goal_id: int | None = None,
        question_count: int = 10,
    ) -> dict:
        safe_count = max(3, min(int(question_count), 30))
        effective_goal_id = goal_id
        if effective_goal_id is None:
            effective_goal_id = await self.diagnostic_repository.latest_goal_id_for_user(
                user_id=user_id,
                tenant_id=tenant_id,
            )
        if effective_goal_id is None:
            raise ValidationError("goal_id is required to persist a smart test when the learner has no prior diagnostic history")
        goal = await self.goal_repository.get_by_id(tenant_id=tenant_id, goal_id=int(effective_goal_id))
        if goal is None:
            raise ValidationError("Goal not found")

        topic_scores = await self.topic_score_repository.list_by_user(tenant_id=tenant_id, user_id=user_id)
        if not topic_scores:
            raise ValidationError("No topic mastery data found for this learner")

        answered_question_ids = await self.diagnostic_repository.answered_question_ids_for_user(
            user_id=user_id,
            tenant_id=tenant_id,
        )
        weak_topic_rows = [row for row in topic_scores if float(row.score) < 80.0]
        if not weak_topic_rows:
            weak_topic_rows = topic_scores[: min(len(topic_scores), 5)]

        target_topic_ids = [int(row.topic_id) for row in weak_topic_rows[:8]]
        topic_map = {
            int(topic.id): topic
            for topic in await self.topic_repository.list_topics_by_ids(target_topic_ids, tenant_id=tenant_id)
        }
        candidate_questions = await self.topic_repository.list_questions_for_topics(
            tenant_id=tenant_id,
            topic_ids=target_topic_ids,
            exclude_question_ids=answered_question_ids,
            goal_id=effective_goal_id,
        )
        if not candidate_questions and goal_id is not None:
            candidate_questions = await self.topic_repository.list_questions_for_topics(
                tenant_id=tenant_id,
                topic_ids=target_topic_ids,
                exclude_question_ids=answered_question_ids,
                goal_id=None,
            )
        if not candidate_questions:
            raise ValidationError("No fresh questions available for the learner's weak topics")

        questions_by_topic: dict[int, dict[int, list[object]]] = defaultdict(lambda: defaultdict(list))
        for question in candidate_questions:
            questions_by_topic[int(question.topic_id)][int(question.difficulty)].append(question)

        selected_questions: list[object] = []
        selected_ids: set[int] = set()
        difficulty_mix = {"easy": 0, "medium": 0, "hard": 0}
        topic_selection_counts: dict[int, int] = defaultdict(int)
        topic_plans: list[dict] = []

        per_topic_target = max(1, safe_count // max(1, min(len(weak_topic_rows), safe_count)))
        for row in weak_topic_rows:
            topic_id = int(row.topic_id)
            topic_name = getattr(topic_map.get(topic_id), "name", f"Topic {topic_id}")
            target_difficulty = self._target_difficulty(
                mastery_score=float(row.score),
                confidence=float(getattr(row, "confidence", 0.5) or 0.5),
            )
            preferred_difficulties = self._difficulty_preference(target_difficulty)
            taken_for_topic = 0
            for difficulty in preferred_difficulties:
                for question in questions_by_topic.get(topic_id, {}).get(difficulty, []):
                    if int(question.id) in selected_ids:
                        continue
                    selected_questions.append(question)
                    selected_ids.add(int(question.id))
                    difficulty_mix[self._difficulty_label(int(question.difficulty))] += 1
                    topic_selection_counts[topic_id] += 1
                    taken_for_topic += 1
                    if len(selected_questions) >= safe_count or taken_for_topic >= per_topic_target:
                        break
                if len(selected_questions) >= safe_count or taken_for_topic >= per_topic_target:
                    break
            topic_plans.append(
                {
                    "topic_id": topic_id,
                    "topic_name": str(topic_name),
                    "mastery_score": round(float(row.score), 2),
                    "confidence": round(float(getattr(row, "confidence", 0.5) or 0.5), 4),
                    "target_difficulty": int(target_difficulty),
                    "selected_question_count": int(topic_selection_counts.get(topic_id, 0)),
                }
            )
            if len(selected_questions) >= safe_count:
                break

        if len(selected_questions) < safe_count:
            fallback_topic_ids = sorted({int(question.topic_id) for question in candidate_questions})
            for topic_id in fallback_topic_ids:
                for difficulty in (2, 1, 3):
                    for question in questions_by_topic.get(topic_id, {}).get(difficulty, []):
                        if int(question.id) in selected_ids:
                            continue
                        selected_questions.append(question)
                        selected_ids.add(int(question.id))
                        difficulty_mix[self._difficulty_label(int(question.difficulty))] += 1
                        topic_selection_counts[topic_id] += 1
                        if len(selected_questions) >= safe_count:
                            break
                    if len(selected_questions) >= safe_count:
                        break
                if len(selected_questions) >= safe_count:
                    break

        if not selected_questions:
            raise ValidationError("Unable to build a smart test from the available question pool")

        started_at = datetime.now(timezone.utc)
        test = await self.diagnostic_repository.create_test(
            user_id=user_id,
            goal_id=int(effective_goal_id),
            started_at=started_at,
        )
        planned_question_ids = [int(question.id) for question in selected_questions]
        await self.diagnostic_repository.upsert_test_state(
            test_id=int(test.id),
            tenant_id=tenant_id,
            user_id=user_id,
            goal_id=int(effective_goal_id),
            answered_question_ids=[],
            previous_answers=[],
            planned_question_ids=planned_question_ids,
            expected_next_question_id=planned_question_ids[0] if planned_question_ids else None,
            updated_at=started_at,
        )
        await self.session.commit()

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "goal_id": int(effective_goal_id),
            "test_id": int(test.id),
            "started_at": started_at.isoformat(),
            "next_question_id": planned_question_ids[0] if planned_question_ids else None,
            "persisted_session": True,
            "question_count": len(selected_questions),
            "generated_from_weak_topics": topic_plans,
            "difficulty_mix": difficulty_mix,
            "repeated_question_count": 0,
            "questions": [
                {
                    "id": int(question.id),
                    "topic_id": int(question.topic_id),
                    "topic_name": str(getattr(topic_map.get(int(question.topic_id)), "name", f"Topic {question.topic_id}")),
                    "difficulty": int(question.difficulty),
                    "difficulty_label": self._difficulty_label(int(question.difficulty)),
                    "question_type": str(question.question_type),
                    "question_text": str(question.question_text),
                    "answer_options": list(question.answer_options or []),
                }
                for question in selected_questions
            ],
        }
