from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_photo_url: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    college_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year_of_study: Mapped[int | None] = mapped_column(Integer, nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    github_repo_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    github_languages: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    github_activity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    leetcode_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    hackerrank_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    daily_study_time: Mapped[str | None] = mapped_column(String(64), nullable=True)
    learning_style: Mapped[str | None] = mapped_column(String(64), nullable=True)
    learning_goal_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_timeline: Mapped[str | None] = mapped_column(String(128), nullable=True)
    profile_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="profile")
