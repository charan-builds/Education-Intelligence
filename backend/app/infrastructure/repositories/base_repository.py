from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def apply_pagination(stmt: Select, limit: int, offset: int) -> Select:
        return stmt.limit(limit).offset(offset)
