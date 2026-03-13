from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import ValidationError
from app.core.pagination import decode_cursor, encode_cursor
from app.infrastructure.repositories.goal_repository import GoalRepository


class GoalService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = GoalRepository(session)

    async def list_goals_page(self, limit: int, offset: int, cursor: str | None = None) -> dict:
        try:
            cursor_id = decode_cursor(cursor) if cursor else None
        except ValueError as exc:
            raise ValidationError("Invalid cursor") from exc

        items = await self.repository.list_all(limit=limit, offset=offset, cursor_id=cursor_id)
        total = await self.repository.count_all()
        next_cursor = encode_cursor(items[-1].id) if items and len(items) == limit else None
        next_offset = offset + limit if (offset + limit) < total else None
        return {
            "items": items,
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": next_cursor,
            },
        }
