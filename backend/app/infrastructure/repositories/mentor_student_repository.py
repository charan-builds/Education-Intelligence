from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.mentor_student import MentorStudent


class MentorStudentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_mapping(self, *, tenant_id: int, mentor_id: int, student_id: int) -> MentorStudent | None:
        result = await self.session.execute(
            select(MentorStudent).where(
                MentorStudent.tenant_id == tenant_id,
                MentorStudent.mentor_id == mentor_id,
                MentorStudent.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def has_mapping(self, *, tenant_id: int, mentor_id: int, student_id: int) -> bool:
        return await self.get_mapping(tenant_id=tenant_id, mentor_id=mentor_id, student_id=student_id) is not None

    async def list_student_ids_for_mentor(self, *, tenant_id: int, mentor_id: int) -> list[int]:
        result = await self.session.execute(
            select(MentorStudent.student_id)
            .where(MentorStudent.tenant_id == tenant_id, MentorStudent.mentor_id == mentor_id)
            .order_by(MentorStudent.student_id.asc())
        )
        return [int(student_id) for student_id in result.scalars().all()]

    async def create_mapping(self, *, tenant_id: int, mentor_id: int, student_id: int) -> MentorStudent:
        existing = await self.get_mapping(tenant_id=tenant_id, mentor_id=mentor_id, student_id=student_id)
        if existing is not None:
            return existing
        row = MentorStudent(
            tenant_id=tenant_id,
            mentor_id=mentor_id,
            student_id=student_id,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.flush()
        return row
