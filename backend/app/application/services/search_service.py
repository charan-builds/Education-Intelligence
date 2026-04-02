from __future__ import annotations

import json

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.sanitization import sanitize_text
from app.domain.models.content_metadata import ContentMetadata
from app.domain.models.file_asset import FileAsset
from app.domain.models.resource import Resource
from app.domain.models.roadmap import Roadmap
from app.domain.models.roadmap_step import RoadmapStep
from app.domain.models.topic import Topic
from app.domain.models.user import User
from app.infrastructure.repositories.tenant_scoping import user_belongs_to_tenant
from app.infrastructure.clients.search_client import SearchClient, SearchClientError


class SearchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.search_client = SearchClient()

    async def search(self, *, tenant_id: int, query: str, limit: int = 10) -> dict:
        normalized_query = sanitize_text(query, max_length=200)
        backend = self.settings.search_backend.lower()
        if backend != "db":
            try:
                items = self.search_client.search(tenant_id=tenant_id, query=normalized_query, limit=limit)
                return {"backend": backend, "items": items}
            except SearchClientError:
                backend = "db"

        pattern = f"%{normalized_query}%"
        topics = (
            await self.session.execute(
                select(Topic.id, Topic.name, Topic.description)
                .where(
                    Topic.tenant_id == tenant_id,
                    or_(Topic.name.ilike(pattern), Topic.description.ilike(pattern)),
                )
                .limit(limit)
            )
        ).all()
        resources = (
            await self.session.execute(
                select(Resource.id, Resource.title, Resource.description, ContentMetadata.tags_json)
                .outerjoin(
                    ContentMetadata,
                    (ContentMetadata.resource_id == Resource.id) & (ContentMetadata.tenant_id == tenant_id),
                )
                .where(
                    Resource.tenant_id == tenant_id,
                    or_(Resource.title.ilike(pattern), Resource.description.ilike(pattern)),
                )
                .limit(limit)
            )
        ).all()
        roadmap_steps = (
            await self.session.execute(
                select(RoadmapStep.id, Topic.name, RoadmapStep.rationale)
                .join(Topic, Topic.id == RoadmapStep.topic_id)
                .join(Roadmap, Roadmap.id == RoadmapStep.roadmap_id)
                .join(User, User.id == Roadmap.user_id)
                .where(
                    user_belongs_to_tenant(User, tenant_id),
                    or_(Topic.name.ilike(pattern), RoadmapStep.rationale.ilike(pattern)),
                )
                .limit(limit)
            )
        ).all()
        return {
            "backend": "db",
            "items": [
                *[
                    {"type": "topic", "id": int(item.id), "title": item.name, "snippet": item.description or ""}
                    for item in topics
                ],
                *[
                    {
                        "type": "resource",
                        "id": int(item.id),
                        "title": item.title,
                        "snippet": item.description or "",
                        "tags": json.loads(item.tags_json or "[]"),
                    }
                    for item in resources
                ],
                *[
                    {"type": "roadmap_step", "id": int(item.id), "title": item.name, "snippet": item.rationale or ""}
                    for item in roadmap_steps
                ],
                *[
                    {
                        "type": "file_asset",
                        "id": int(item.id),
                        "title": item.filename,
                        "snippet": item.description or "",
                        "tags": json.loads(item.tags_json or "[]"),
                        "cdn_url": item.cdn_url,
                    }
                    for item in (
                        await self.session.execute(
                            select(FileAsset.id, FileAsset.filename, FileAsset.cdn_url, ContentMetadata.description, ContentMetadata.tags_json)
                            .outerjoin(
                                ContentMetadata,
                                (ContentMetadata.file_asset_id == FileAsset.id) & (ContentMetadata.tenant_id == tenant_id),
                            )
                            .where(
                                FileAsset.tenant_id == tenant_id,
                                or_(FileAsset.filename.ilike(pattern), ContentMetadata.description.ilike(pattern)),
                            )
                            .limit(limit)
                        )
                    ).all()
                ],
            ][: limit * 3],
        }
