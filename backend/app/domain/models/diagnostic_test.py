from datetime import datetime
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class DiagnosticTestStatus(str, Enum):
    started = "started"
    in_progress = "in_progress"
    submitted = "submitted"
    expired = "expired"
    abandoned = "abandoned"


class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"
    __table_args__ = (
        CheckConstraint("test_duration > 0", name="ck_diagnostic_tests_test_duration_positive"),
        CheckConstraint(
            "status IN ('started', 'in_progress', 'submitted', 'expired', 'abandoned')",
            name="ck_diagnostic_tests_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id", ondelete="RESTRICT"), index=True)
    status: Mapped[str] = mapped_column(
        String(length=32),
        nullable=False,
        default=DiagnosticTestStatus.started.value,
        server_default=DiagnosticTestStatus.started.value,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    test_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=20, server_default="20")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="diagnostic_tests")
    goal = relationship("Goal")
    answers = relationship("UserAnswer", back_populates="test", cascade="all, delete-orphan")
