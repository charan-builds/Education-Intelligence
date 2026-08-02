from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class LearningProfile(Base):
    __tablename__ = "learning_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    profile_type: Mapped[str] = mapped_column(String(64), nullable=False, default="balanced")
    learning_speed: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    difficulty_preference: Mapped[str] = mapped_column(String(32), nullable=False, default="moderate")
    recommendation_bias: Mapped[str] = mapped_column(String(64), nullable=False, default="foundations_first")

    user = relationship("User", back_populates="learning_profile", uselist=False)
