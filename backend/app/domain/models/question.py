from sqlalchemy import ForeignKey, Integer, JSON, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String(32), nullable=False, default="short_text")
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    accepted_answers: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    answer_options: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    topic = relationship("Topic", back_populates="questions")


def validate_question_configuration(question: Question) -> None:
    supported_types = {"multiple_choice", "short_text"}
    if question.question_type not in supported_types:
        raise ValueError(f"Unsupported question_type: {question.question_type}")

    answer_options = list(question.answer_options or [])
    if question.question_type == "multiple_choice" and not answer_options:
        raise ValueError("multiple_choice questions require non-empty answer_options")
    if question.question_type == "short_text" and answer_options:
        raise ValueError("short_text questions must not define answer_options")


@event.listens_for(Question, "before_insert")
def _validate_question_before_insert(_mapper, _connection, target: Question) -> None:
    validate_question_configuration(target)


@event.listens_for(Question, "before_update")
def _validate_question_before_update(_mapper, _connection, target: Question) -> None:
    validate_question_configuration(target)
