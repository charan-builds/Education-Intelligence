from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.application.exceptions import ValidationError
from app.application.services.diagnostic.completion_orchestrator import DiagnosticCompletionOrchestrator
from app.application.services.diagnostic.selection_service import AdaptiveSelectionService
from app.application.services.diagnostic.test_service import DiagnosticTestService


class _Session:
    def __init__(self):
        self.commit_called = False
        self.rollback_called = False

    async def commit(self):
        self.commit_called = True

    async def rollback(self):
        self.rollback_called = True


class _DiagnosticRepository:
    def __init__(self, test, answers=None):
        self.test = test
        self.answers = list(answers or [])
        self.expired_at = None
        self.answer_write_attempted = False
        self.completed = False

    async def get_test_for_user(self, test_id, user_id, tenant_id, for_update=False):
        _ = test_id, user_id, tenant_id, for_update
        return self.test

    async def list_answers_for_test(self, *, test_id):
        _ = test_id
        return self.answers

    async def expire_test(self, test, expired_at):
        self.expired_at = expired_at
        test.expired_at = expired_at
        return test

    async def upsert_answer(self, **kwargs):
        _ = kwargs
        self.answer_write_attempted = True
        raise AssertionError("late submissions must not write answers")

    async def complete_test(self, test, completed_at):
        _ = completed_at
        self.completed = True
        test.completed_at = completed_at
        return test


def _test_row(*, started_delta: timedelta, test_duration: int = 20, expired_at=None):
    return SimpleNamespace(
        id=55,
        user_id=7,
        goal_id=9,
        started_at=datetime.now(timezone.utc) - started_delta,
        test_duration=test_duration,
        completed_at=None,
        expired_at=expired_at,
    )


@pytest.mark.asyncio
async def test_submit_answers_marks_expired_and_rejects_late_submission():
    session = _Session()
    test = _test_row(started_delta=timedelta(minutes=21), test_duration=20)
    repository = _DiagnosticRepository(test)
    orchestrator = DiagnosticCompletionOrchestrator(session, diagnostic_repository=repository)

    with pytest.raises(ValidationError, match="Diagnostic test expired"):
        await orchestrator.submit_answers(
            test_id=55,
            user_id=7,
            tenant_id=3,
            answers=[{"question_id": 101, "selected_answer": "A", "time_taken": 10}],
        )

    assert repository.expired_at is not None
    assert test.expired_at == repository.expired_at
    assert test.completed_at is None
    assert repository.answer_write_attempted is False
    assert repository.completed is False
    assert session.commit_called is True


@pytest.mark.asyncio
async def test_finalize_marks_expired_even_when_no_answers_were_submitted():
    session = _Session()
    test = _test_row(started_delta=timedelta(minutes=45), test_duration=20)
    repository = _DiagnosticRepository(test)
    orchestrator = DiagnosticCompletionOrchestrator(session, diagnostic_repository=repository)

    with pytest.raises(ValidationError, match="Diagnostic test expired"):
        await orchestrator.finalize_test(test_id=55, user_id=7, tenant_id=3)

    assert repository.expired_at is not None
    assert test.completed_at is None
    assert repository.completed is False
    assert session.commit_called is True


@pytest.mark.asyncio
async def test_answer_question_marks_expired_and_rejects_late_request():
    session = _Session()
    test = _test_row(started_delta=timedelta(minutes=21), test_duration=20)
    repository = _DiagnosticRepository(test)
    service = DiagnosticTestService(
        session,
        diagnostic_repository=repository,
        topic_repository=SimpleNamespace(),
    )

    with pytest.raises(ValidationError, match="Diagnostic test expired"):
        await service.answer_question(
            test_id=55,
            user_id=7,
            tenant_id=3,
            question_id=101,
            user_answer="A",
            time_taken=10,
        )

    assert repository.expired_at is not None
    assert test.expired_at == repository.expired_at
    assert repository.answer_write_attempted is False
    assert session.commit_called is True


@pytest.mark.asyncio
async def test_next_question_marks_expired_and_rejects_late_request():
    class _TopicRepository:
        async def list_questions_by_ids(self, **kwargs):
            _ = kwargs
            raise AssertionError("late next-question requests must not select questions")

    session = _Session()
    test = _test_row(started_delta=timedelta(minutes=21), test_duration=20)
    repository = _DiagnosticRepository(test)
    service = AdaptiveSelectionService(
        session,
        diagnostic_repository=repository,
        topic_repository=_TopicRepository(),
    )

    with pytest.raises(ValidationError, match="Diagnostic test expired"):
        await service.get_next_question(test_id=55, user_id=7, tenant_id=3)

    assert repository.expired_at is not None
    assert test.expired_at == repository.expired_at
    assert session.commit_called is True


@pytest.mark.asyncio
async def test_submit_answers_rejects_already_expired_test_without_scoring():
    session = _Session()
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    test = _test_row(started_delta=timedelta(minutes=5), test_duration=20, expired_at=expired_at)
    repository = _DiagnosticRepository(test)
    orchestrator = DiagnosticCompletionOrchestrator(session, diagnostic_repository=repository)

    with pytest.raises(ValidationError, match="Diagnostic test expired"):
        await orchestrator.submit_answers(
            test_id=55,
            user_id=7,
            tenant_id=3,
            answers=[{"question_id": 101, "selected_answer": "A", "time_taken": 10}],
        )

    assert repository.expired_at is None
    assert repository.answer_write_attempted is False
    assert repository.completed is False
