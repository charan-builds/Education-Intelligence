from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.domain.models.base import Base


class UserAnswer(Base):
    __tablename__ = "user_answers"
    __table_args__ = (UniqueConstraint("test_id", "question_id", name="uq_user_answers_test_question"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_tests.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    selected_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    time_taken: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    test = relationship("DiagnosticTest", back_populates="answers")
    question = relationship("Question", back_populates="user_answers")

    user_answer = synonym("selected_answer")
