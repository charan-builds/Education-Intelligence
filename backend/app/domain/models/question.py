from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Index,
    JSON,
    String,
    Text,
    event,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class QuestionDifficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

    def __int__(self) -> int:
        return {self.easy: 1, self.medium: 2, self.hard: 3}[self]


class QuestionType(str, Enum):
    mcq = "mcq"


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint("difficulty_level BETWEEN 1 AND 3", name="ck_questions_difficulty_level"),
        CheckConstraint("difficulty_label IN ('easy', 'medium', 'hard')", name="ck_questions_difficulty_label"),
        CheckConstraint("version >= 1", name="ck_questions_version_positive"),
        Index("ix_questions_topic_difficulty_level_active_id", "topic_id", "difficulty_level", "is_active", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true", index=True)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False, default=2, server_default="2", index=True)
    difficulty_label: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="medium",
        server_default="medium",
        index=True,
    )
    question_type: Mapped[QuestionType] = mapped_column(SQLEnum(QuestionType), nullable=False, default=QuestionType.mcq)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    accepted_answers: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    topic = relationship("Topic", back_populates="questions")
    user_answers = relationship("UserAnswer", back_populates="question", passive_deletes="all")
    option_rows = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.position",
    )

    @property
    def options(self) -> list[dict]:
        return [
            {
                "key": option.option_key,
                "text": option.option_text,
                "is_correct": bool(option.is_correct),
            }
            for option in sorted(self.option_rows, key=lambda item: (int(item.position or 0), str(item.option_key)))
        ]

    @options.setter
    def options(self, values: list[dict] | list[str] | None) -> None:
        self.option_rows = build_question_options(values, correct_answer=getattr(self, "correct_answer", None))

    @property
    def answer_options(self) -> list[str]:
        return [option["text"] for option in self.options]

    @answer_options.setter
    def answer_options(self, values: list[dict] | list[str] | None) -> None:
        self.options = values

    @hybrid_property
    def difficulty(self) -> int:
        return int(self.difficulty_level or 2)

    @difficulty.inplace.expression
    @classmethod
    def _difficulty_expression(cls):
        return cls.difficulty_level

    @difficulty.setter
    def difficulty(self, value: int | str | QuestionDifficulty) -> None:
        level, label = normalize_difficulty(value)
        self.difficulty_level = level
        self.difficulty_label = label


def normalize_difficulty(value: int | str | QuestionDifficulty | None) -> tuple[int, str]:
    if value is None:
        return 2, "medium"
    if isinstance(value, QuestionDifficulty):
        value = value.value
    normalized = str(value).strip().lower()
    labels_by_level = {1: "easy", 2: "medium", 3: "hard"}
    levels_by_label = {label: level for level, label in labels_by_level.items()}
    if normalized.isdigit():
        level = max(1, min(3, int(normalized)))
        return level, labels_by_level[level]
    label = normalized if normalized in levels_by_label else "medium"
    return levels_by_label[label], label


def _option_key(index: int) -> str:
    if 0 <= index < 26:
        return chr(ord("A") + index)
    return str(index + 1)


def _normalize_option_item(item: object, index: int, correct_answer: str | None) -> dict:
    key = _option_key(index)
    text = ""
    is_correct = False
    if isinstance(item, dict):
        key = str(item.get("key") or item.get("option_key") or key).strip() or key
        text = str(item.get("text") or item.get("option_text") or item.get("label") or item.get("value") or "").strip()
        is_correct = bool(item.get("is_correct", False))
    else:
        text = str(item or "").strip()

    if correct_answer is not None and text and text == str(correct_answer).strip():
        is_correct = True
    return {"key": key, "text": text, "is_correct": is_correct}


def build_question_options(values: list[dict] | list[str] | None, correct_answer: str | None = None) -> list["QuestionOption"]:
    from app.domain.models.question_option import QuestionOption

    rows: list[QuestionOption] = []
    seen_keys: set[str] = set()
    for index, item in enumerate(values or []):
        normalized = _normalize_option_item(item, index, correct_answer)
        key = normalized["key"]
        text = normalized["text"]
        if not text:
            continue
        if key in seen_keys:
            key = _option_key(index)
        seen_keys.add(key)
        rows.append(
            QuestionOption(
                option_key=key,
                option_text=text,
                is_correct=bool(normalized["is_correct"]),
                position=index,
            )
        )
    return rows


def _question_type_value(value: object) -> str:
    return str(value.value if hasattr(value, "value") else value).strip().lower()


def validate_question_configuration(question: Question) -> None:
    if getattr(question, "difficulty_level", None) is None or getattr(question, "difficulty_label", None) is None:
        source = getattr(question, "difficulty_label", None) or getattr(question, "difficulty_level", None)
        question.difficulty_level, question.difficulty_label = normalize_difficulty(source)
    else:
        question.difficulty_level, question.difficulty_label = normalize_difficulty(question.difficulty_level)

    question_type = _question_type_value(question.question_type)
    if question_type not in {"mcq", "multiple_choice", "short_text"}:
        raise ValueError(f"Unsupported question_type: {question.question_type}")

    if getattr(question, "accepted_answers", None) is None:
        question.accepted_answers = []

    answer_options = list(question.options or [])
    if question_type in {"mcq", "multiple_choice"}:
        if not answer_options:
            raise ValueError("multiple_choice questions require non-empty answer_options")
        question.question_type = QuestionType.mcq
        return

    if answer_options:
        raise ValueError("short_text questions must not define answer_options")
    raise ValueError("Unsupported question_type: short_text")


@event.listens_for(Question, "before_insert")
def _validate_question_before_insert(_mapper, _connection, target: Question) -> None:
    validate_question_configuration(target)


@event.listens_for(Question, "before_update")
def _validate_question_before_update(_mapper, _connection, target: Question) -> None:
    validate_question_configuration(target)
