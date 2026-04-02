from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.services import diagnostic_rules


class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id", ondelete="RESTRICT"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="diagnostic_tests")
    answers = relationship("UserAnswer", back_populates="test", cascade="all, delete-orphan")

    @staticmethod
    def _normalize_answer(value: str) -> str:
        return diagnostic_rules.normalize_answer(value)

    @classmethod
    def evaluate_answers(cls, answers: list[dict], questions_by_id: dict[int, object]) -> list[dict]:
        return diagnostic_rules.evaluate_answers(answers, questions_by_id)

    @staticmethod
    def accuracy_from_score(score: float) -> float:
        return diagnostic_rules.accuracy_from_score(score)

    @classmethod
    def build_adaptive_rows(cls, *, answers: list[object], questions_by_id: dict[int, object]) -> list[dict]:
        return diagnostic_rules.build_adaptive_rows(answers=answers, questions_by_id=questions_by_id)
