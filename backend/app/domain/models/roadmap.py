from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.services import roadmap_rules


class Roadmap(Base):
    __tablename__ = "roadmaps"
    __table_args__ = (
        UniqueConstraint("user_id", "goal_id", "test_id", name="uq_roadmaps_user_goal_test"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id", ondelete="RESTRICT"), index=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_tests.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(length=32), nullable=False, default="generating")
    error_message: Mapped[str | None] = mapped_column(String(length=500), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="roadmaps")
    steps = relationship("RoadmapStep", back_populates="roadmap", cascade="all, delete-orphan")

    @staticmethod
    def generate_steps(
        *,
        topic_order: list[int],
        topic_scores: dict[int, float],
        dependency_depths: dict[int, int],
        weakness_clusters: list[dict],
        profile_type: str,
        response_times: list[float] | None,
        base_date: datetime,
    ) -> list[dict]:
        return roadmap_rules.generate_steps(
            topic_order=topic_order,
            topic_scores=topic_scores,
            dependency_depths=dependency_depths,
            weakness_clusters=weakness_clusters,
            profile_type=profile_type,
            response_times=response_times,
            base_date=base_date,
        )
