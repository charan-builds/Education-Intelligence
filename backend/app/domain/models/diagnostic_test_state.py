from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class DiagnosticTestState(Base):
    __tablename__ = "diagnostic_test_states"
    __table_args__ = (
        UniqueConstraint("test_id", name="uq_diagnostic_test_states_test_id"),
    )

    test_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_tests.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    goal_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    answered_question_ids: Mapped[list[int]] = mapped_column(JSONB, nullable=False, default=list)
    previous_answers: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    planned_question_ids: Mapped[list[int]] = mapped_column(JSONB, nullable=False, default=list)
    expected_next_question_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    test = relationship("DiagnosticTest", lazy="joined")
