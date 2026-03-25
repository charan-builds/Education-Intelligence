from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class UserRole(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    teacher = "teacher"
    mentor = "mentor"
    student = "student"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)
    experience_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    focus_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tenant = relationship("Tenant", back_populates="users")
    diagnostic_tests = relationship("DiagnosticTest", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="user", cascade="all, delete-orphan")
    topic_scores = relationship("TopicScore", back_populates="user", cascade="all, delete-orphan")
    mentor_suggestions = relationship("MentorSuggestion", back_populates="user", cascade="all, delete-orphan")
    mentor_memory_profiles = relationship("MentorMemoryProfile", back_populates="user", cascade="all, delete-orphan")
    mentor_session_memories = relationship("MentorSessionMemory", back_populates="user", cascade="all, delete-orphan")
    refresh_sessions = relationship("RefreshSession", cascade="all, delete-orphan")
    skill_vectors = relationship("UserSkillVector", cascade="all, delete-orphan")
    notifications = relationship("Notification", cascade="all, delete-orphan")
