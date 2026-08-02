from sqlalchemy import Boolean, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class UserGoal(Base):
    __tablename__ = "user_goals"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "goal_id", name="pk_user_goals"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user = relationship("User", back_populates="user_goals")
    goal = relationship("Goal")
