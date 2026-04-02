from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class TenantType(str, Enum):
    platform = "platform"
    college = "college"
    company = "company"
    school = "school"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    subdomain: Mapped[str | None] = mapped_column(String(63), nullable=True, unique=True, index=True)
    type: Mapped[TenantType] = mapped_column(SQLEnum(TenantType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    user_roles = relationship("UserTenantRole", back_populates="tenant", cascade="all, delete-orphan")
