from datetime import datetime

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.models.user import UserRole


class UserTenantRole(Base):
    __tablename__ = "user_tenant_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant_roles_user_tenant"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="tenant_roles")
    tenant = relationship("Tenant", back_populates="user_roles")
