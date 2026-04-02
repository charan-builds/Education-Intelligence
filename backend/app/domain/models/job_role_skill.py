from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class JobRoleSkill(Base):
    __tablename__ = "job_role_skills"
    __table_args__ = (UniqueConstraint("job_role_id", "skill_id", name="uq_job_role_skill"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_role_id: Mapped[int] = mapped_column(ForeignKey("job_roles.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
