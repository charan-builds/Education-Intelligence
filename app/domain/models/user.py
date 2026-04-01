from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, UniqueConstraint
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
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    preferences_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(128), nullable=True)
    experience_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    focus_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tenant = relationship("Tenant", back_populates="users")
    tenant_roles = relationship("UserTenantRole", back_populates="user", cascade="all, delete-orphan")
    diagnostic_tests = relationship("DiagnosticTest", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="user", cascade="all, delete-orphan")
    topic_scores = relationship("TopicScore", back_populates="user", cascade="all, delete-orphan")
    mentor_suggestions = relationship("MentorSuggestion", back_populates="user", cascade="all, delete-orphan")
    mentor_memory_profiles = relationship("MentorMemoryProfile", back_populates="user", cascade="all, delete-orphan")
    mentor_session_memories = relationship("MentorSessionMemory", back_populates="user", cascade="all, delete-orphan")
    refresh_sessions = relationship("RefreshSession", cascade="all, delete-orphan")
    sessions = relationship("SessionRecord", cascade="all, delete-orphan")
    skill_vectors = relationship("UserSkillVector", cascade="all, delete-orphan")
    notifications = relationship("Notification", cascade="all, delete-orphan")
    gamification_profile = relationship("GamificationProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    gamification_events = relationship("GamificationEvent", back_populates="user", cascade="all, delete-orphan")
