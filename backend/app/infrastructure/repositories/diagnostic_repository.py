from datetime import datetime
from random import randint, shuffle

from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import lazyload, selectinload

from app.domain.models.diagnostic_test import DiagnosticTest, DiagnosticTestStatus
from app.domain.models.diagnostic_test_state import DiagnosticTestState
from app.domain.models.goal_topic import GoalTopic
from app.domain.models.question import Question, QuestionDifficulty
from app.domain.models.topic import Topic
from app.domain.models.user_answer import UserAnswer
from app.infrastructure.repositories.tenant_scoping import tenant_user_scope


class DiagnosticRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _topic_id(topic: int | Topic | object) -> int:
        return int(topic if isinstance(topic, int) else getattr(topic, "id"))

    @staticmethod
    def _difficulty_key(difficulty: object) -> str:
        if isinstance(difficulty, QuestionDifficulty):
            return difficulty.value
        value = str(difficulty).lower()
        return {"1": "easy", "2": "medium", "3": "hard"}.get(value, value)

    @staticmethod
    def _difficulty_targets(total_questions: int) -> dict[str, int]:
        easy_count = int(total_questions * 0.4)
        medium_count = int(total_questions * 0.4)
        hard_count = total_questions - easy_count - medium_count
        return {"easy": easy_count, "medium": medium_count, "hard": hard_count}

    async def _sample_questions(
        self,
        *,
        goal_id: int,
        topic_ids: list[int],
        limit: int,
        difficulty: str | None = None,
        exclude_question_ids: set[int] | None = None,
    ) -> list[Question]:
        if not topic_ids or limit <= 0:
            return []

        criteria = [
            Question.topic_id.in_(topic_ids),
            Question.topic_id.in_(select(GoalTopic.topic_id).where(GoalTopic.goal_id == goal_id)),
            Question.is_active.is_(True),
        ]
        if difficulty is not None:
            criteria.append(Question.difficulty_label == difficulty)
        if exclude_question_ids:
            criteria.append(~Question.id.in_(sorted(int(question_id) for question_id in exclude_question_ids)))

        count_result = await self.session.execute(select(func.count()).select_from(Question).where(*criteria))
        row_count = int(count_result.scalar_one() or 0)
        if row_count <= 0:
            return []

        bounded_limit = min(int(limit), row_count)
        offset = randint(0, row_count - bounded_limit) if row_count > bounded_limit else 0
        stmt = (
            select(Question)
            .options(selectinload(Question.option_rows))
            .where(*criteria)
            .order_by(Question.id.asc())
            .offset(offset)
            .limit(bounded_limit)
        )
        result = await self.session.execute(stmt)
        questions = list(result.scalars().all())
        shuffle(questions)
        return questions

    async def generate_diagnostic_test_questions(
        self,
        *,
        goal_id: int,
        topics: list[int | Topic | object],
        total_questions: int = 20,
    ) -> list[Question]:
        """Generate a randomized diagnostic test while preserving topic coverage.

        Selection target is 40% easy, 40% medium, and 20% hard. If the bank is
        sparse, the generator falls back across difficulties without duplicating
        questions so the test still has the best available topic coverage.
        """
        topic_ids = list(dict.fromkeys(self._topic_id(topic) for topic in topics))
        if not topic_ids:
            return []

        question_limit = max(1, min(int(total_questions), 20))
        coverage_topic_ids = topic_ids[:question_limit]
        targets = self._difficulty_targets(question_limit)
        remaining = dict(targets)

        selected: list[Question] = []
        selected_ids: set[int] = set()

        def add_question(question: Question) -> bool:
            if int(question.id) in selected_ids or len(selected) >= question_limit:
                return False
            selected.append(question)
            selected_ids.add(int(question.id))
            difficulty = self._difficulty_key(question.difficulty_label)
            if difficulty in remaining and remaining[difficulty] > 0:
                remaining[difficulty] -= 1
            return True

        async def sample_and_add(
            sample_topic_ids: list[int],
            *,
            difficulty: str | None = None,
            limit: int = 1,
        ) -> bool:
            questions = await self._sample_questions(
                goal_id=goal_id,
                topic_ids=sample_topic_ids,
                limit=limit,
                difficulty=difficulty,
                exclude_question_ids=selected_ids,
            )
            added = False
            for question in questions:
                added = add_question(question) or added
                if len(selected) >= question_limit:
                    break
            return added

        # First pass: choose at least one question per topic where the bank allows it.
        for topic_id in coverage_topic_ids:
            preferred = sorted(
                ("easy", "medium", "hard"),
                key=lambda difficulty: remaining.get(difficulty, 0),
                reverse=True,
            )
            for difficulty in preferred:
                if await sample_and_add([topic_id], difficulty=difficulty):
                    break
            else:
                await sample_and_add([topic_id])

        # Second pass: fill the requested difficulty distribution as closely as possible.
        for difficulty in ("easy", "medium", "hard"):
            while remaining[difficulty] > 0 and len(selected) < question_limit:
                added = await sample_and_add(
                    topic_ids,
                    difficulty=difficulty,
                    limit=min(remaining[difficulty], question_limit - len(selected)),
                )
                if not added:
                    break

        # Final sparse-bank fallback: fill with any remaining unique candidates.
        while len(selected) < question_limit:
            added = await sample_and_add(topic_ids, limit=question_limit - len(selected))
            if not added:
                break

        shuffle(selected)
        return selected

    async def create_test(self, user_id: int, goal_id: int, started_at: datetime) -> DiagnosticTest:
        test = DiagnosticTest(
            user_id=user_id,
            goal_id=goal_id,
            status=DiagnosticTestStatus.started.value,
            started_at=started_at,
            completed_at=None,
        )
        self.session.add(test)
        await self.session.flush()
        return test

    async def get_test_for_user(
        self,
        test_id: int,
        user_id: int,
        tenant_id: int,
        *,
        for_update: bool = False,
    ) -> DiagnosticTest | None:
        stmt = (
            select(DiagnosticTest)
            .join(DiagnosticTest.user)
            .where(
                DiagnosticTest.id == test_id,
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_open_test_for_user(self, *, user_id: int, goal_id: int, tenant_id: int) -> DiagnosticTest | None:
        result = await self.session.execute(
            select(DiagnosticTest)
            .join(DiagnosticTest.user)
            .where(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.goal_id == goal_id,
                DiagnosticTest.status.in_(
                    (
                        DiagnosticTestStatus.started.value,
                        DiagnosticTestStatus.in_progress.value,
                    )
                ),
                DiagnosticTest.completed_at.is_(None),
                DiagnosticTest.expired_at.is_(None),
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .order_by(DiagnosticTest.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def latest_goal_id_for_user(self, *, user_id: int, tenant_id: int) -> int | None:
        result = await self.session.execute(
            select(DiagnosticTest.goal_id)
            .join(DiagnosticTest.user)
            .where(
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .order_by(DiagnosticTest.id.desc())
            .limit(1)
        )
        value = result.scalar_one_or_none()
        return int(value) if value is not None else None

    async def list_answers_for_test(self, *, test_id: int) -> list[UserAnswer]:
        result = await self.session.execute(
            select(UserAnswer).where(UserAnswer.test_id == test_id).order_by(UserAnswer.id.asc())
        )
        return list(result.scalars().all())

    async def get_test_state(
        self,
        *,
        test_id: int,
        user_id: int,
        tenant_id: int,
        for_update: bool = False,
    ) -> DiagnosticTestState | None:
        stmt = (
            select(DiagnosticTestState)
            .options(lazyload(DiagnosticTestState.test))
            .join(DiagnosticTest, DiagnosticTest.id == DiagnosticTestState.test_id)
            .join(DiagnosticTest.user)
            .where(
                DiagnosticTestState.test_id == test_id,
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
        )
        if for_update:
            stmt = stmt.with_for_update(of=DiagnosticTestState)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_test_state(
        self,
        *,
        test_id: int,
        tenant_id: int,
        user_id: int,
        goal_id: int,
        answered_question_ids: list[int],
        previous_answers: list[dict],
        planned_question_ids: list[int] | None = None,
        expected_next_question_id: int | None,
        updated_at: datetime,
    ) -> DiagnosticTestState:
        state = await self.session.get(DiagnosticTestState, test_id)
        if state is None:
            state = DiagnosticTestState(
                test_id=test_id,
                tenant_id=tenant_id,
                user_id=user_id,
                goal_id=goal_id,
                answered_question_ids=list(answered_question_ids),
                previous_answers=list(previous_answers),
                planned_question_ids=list(planned_question_ids or []),
                expected_next_question_id=expected_next_question_id,
                updated_at=updated_at,
            )
            self.session.add(state)
            await self.session.flush()
            return state

        state.tenant_id = tenant_id
        state.user_id = user_id
        state.goal_id = goal_id
        state.answered_question_ids = list(answered_question_ids)
        state.previous_answers = list(previous_answers)
        if planned_question_ids is not None:
            state.planned_question_ids = list(planned_question_ids)
        state.expected_next_question_id = expected_next_question_id
        state.updated_at = updated_at
        await self.session.flush()
        return state

    async def get_answer_for_test_question(
        self,
        *,
        test_id: int,
        question_id: int,
        for_update: bool = False,
    ) -> UserAnswer | None:
        stmt = select(UserAnswer).where(UserAnswer.test_id == test_id, UserAnswer.question_id == question_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_answer(
        self,
        test_id: int,
        question_id: int,
        user_answer: str,
        score: float,
        time_taken: float,
        accuracy: float,
        is_correct: bool,
        attempt_count: int = 1,
    ) -> UserAnswer:
        answer = UserAnswer(
            test_id=test_id,
            question_id=question_id,
            user_answer=user_answer,
            is_correct=is_correct,
            score=score,
            time_taken=time_taken,
            accuracy=accuracy,
            attempt_count=attempt_count,
        )
        self.session.add(answer)
        await self.session.flush()
        return answer

    async def upsert_answer(
        self,
        *,
        test_id: int,
        question_id: int,
        user_answer: str,
        score: float,
        time_taken: float,
        accuracy: float,
        is_correct: bool,
        attempt_count: int,
    ) -> UserAnswer:
        existing = await self.get_answer_for_test_question(test_id=test_id, question_id=question_id)
        if existing is not None:
            existing.user_answer = user_answer
            existing.is_correct = is_correct
            existing.score = score
            existing.time_taken = time_taken
            existing.accuracy = accuracy
            existing.attempt_count = attempt_count
            await self.session.flush()
            return existing
        return await self.add_answer(
            test_id=test_id,
            question_id=question_id,
            user_answer=user_answer,
            score=score,
            time_taken=time_taken,
            accuracy=accuracy,
            is_correct=is_correct,
            attempt_count=attempt_count,
        )

    async def complete_test(self, test: DiagnosticTest, completed_at: datetime) -> DiagnosticTest:
        test.status = DiagnosticTestStatus.submitted.value
        test.completed_at = completed_at
        await self.session.flush()
        return test

    async def expire_test(self, test: DiagnosticTest, expired_at: datetime) -> DiagnosticTest:
        test.status = DiagnosticTestStatus.expired.value
        test.expired_at = expired_at
        await self.session.flush()
        return test

    async def mark_test_in_progress(self, test: DiagnosticTest) -> DiagnosticTest:
        if test.status == DiagnosticTestStatus.started.value:
            test.status = DiagnosticTestStatus.in_progress.value
            await self.session.flush()
        return test

    async def abandon_test(self, test: DiagnosticTest) -> DiagnosticTest:
        test.status = DiagnosticTestStatus.abandoned.value
        await self.session.flush()
        return test

    async def topic_scores_for_test(self, test_id: int, user_id: int, tenant_id: int) -> dict[int, float]:
        result = await self.session.execute(
            select(Question.topic_id, func.avg(UserAnswer.score))
            .join(UserAnswer, UserAnswer.question_id == Question.id)
            .join(DiagnosticTest, DiagnosticTest.id == UserAnswer.test_id)
            .where(
                UserAnswer.test_id == test_id,
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .group_by(Question.topic_id)
        )
        return {topic_id: float(avg_score) for topic_id, avg_score in result.all()}

    async def topic_performance_for_test(self, *, test_id: int, user_id: int, tenant_id: int) -> list[dict]:
        result = await self.session.execute(
            select(
                Topic.name.label("topic_name"),
                func.count(UserAnswer.id).label("total_questions"),
                func.coalesce(func.sum(func.cast(UserAnswer.is_correct, Integer)), 0).label("correct_answers"),
                func.avg(UserAnswer.score).label("score_percentage"),
            )
            .join(Question, Question.id == UserAnswer.question_id)
            .join(Topic, Topic.id == Question.topic_id)
            .join(DiagnosticTest, DiagnosticTest.id == UserAnswer.test_id)
            .join(DiagnosticTest.user)
            .where(
                UserAnswer.test_id == test_id,
                DiagnosticTest.user_id == user_id,
                Topic.tenant_id == tenant_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .group_by(Topic.name)
            .order_by(Topic.name.asc())
        )
        return [
            {
                "topic_name": str(row.topic_name),
                "total_questions": int(row.total_questions or 0),
                "correct_answers": int(row.correct_answers or 0),
                "score_percentage": round(float(row.score_percentage or 0.0), 2),
            }
            for row in result.all()
        ]

    async def answer_analytics_for_test(
        self,
        test_id: int,
        user_id: int,
        tenant_id: int,
    ) -> dict:
        result = await self.session.execute(
            select(UserAnswer.time_taken, UserAnswer.score, Question.difficulty_level)
            .join(Question, Question.id == UserAnswer.question_id)
            .join(DiagnosticTest, DiagnosticTest.id == UserAnswer.test_id)
            .where(
                UserAnswer.test_id == test_id,
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .order_by(UserAnswer.id.asc())
        )
        rows = list(result.all())
        distribution = {"easy": 0, "medium": 0, "hard": 0}
        for _, _, difficulty in rows:
            if int(difficulty) <= 1:
                distribution["easy"] += 1
            elif int(difficulty) == 2:
                distribution["medium"] += 1
            else:
                distribution["hard"] += 1

        return {
            "response_times": [float(time_taken) for time_taken, _, _ in rows],
            "accuracies": [float(score) for _, score, _ in rows],
            "difficulty_distribution": distribution,
        }

    async def answered_question_ids_for_user(self, *, user_id: int, tenant_id: int) -> list[int]:
        result = await self.session.execute(
            select(UserAnswer.question_id)
            .join(DiagnosticTest, DiagnosticTest.id == UserAnswer.test_id)
            .join(DiagnosticTest.user)
            .where(
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .distinct()
            .order_by(UserAnswer.question_id.asc())
        )
        return [int(question_id) for question_id in result.scalars().all()]
