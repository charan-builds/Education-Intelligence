from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.models.content_metadata import ContentMetadata
from app.domain.models.file_asset import FileAsset
from app.domain.models.resource import Resource
from app.domain.models.topic import Topic
from app.infrastructure.clients.search_client import SearchClient, SearchClientError


class SearchIndexService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.search_client = SearchClient()
        self.settings = get_settings()

    async def index_topic(self, *, tenant_id: int, topic_id: int) -> None:
        if self.settings.search_backend.lower() == "db":
            return
        topic = await self.session.get(Topic, topic_id)
        if topic is None or int(topic.tenant_id) != int(tenant_id):
            raise ValueError("Topic not found")
        self.search_client.upsert_documents(
            documents=[
                {
                    "id": f"topic:{tenant_id}:{topic_id}",
                    "tenant_id": tenant_id,
                    "entity_type": "topic",
                    "entity_id": topic_id,
                    "title": topic.name,
                    "description": topic.description or "",
                    "tags": [],
                    "body": topic.description or "",
                }
            ]
        )

    async def index_resource(self, *, tenant_id: int, resource_id: int) -> None:
        if self.settings.search_backend.lower() == "db":
            return
        metadata = await self.session.scalar(
            select(ContentMetadata).where(
                ContentMetadata.tenant_id == tenant_id,
                ContentMetadata.resource_id == resource_id,
            )
        )
        resource = await self.session.get(Resource, resource_id)
        if resource is None or int(resource.tenant_id) != int(tenant_id):
            raise ValueError("Resource not found")
        self.search_client.upsert_documents(
            documents=[
                {
                    "id": f"resource:{tenant_id}:{resource_id}",
                    "tenant_id": tenant_id,
                    "entity_type": "resource",
                    "entity_id": resource_id,
                    "topic_id": int(resource.topic_id),
                    "title": (metadata.title if metadata and metadata.title else resource.title),
                    "description": (metadata.description if metadata and metadata.description else (resource.description or "")),
                    "tags": json.loads(metadata.tags_json) if metadata else [],
                    "body": " ".join(
                        item for item in [resource.title, resource.description or "", metadata.description if metadata else ""] if item
                    ),
                    "url": resource.url,
                    "resource_type": resource.resource_type,
                }
            ]
        )

    async def index_file_asset(self, *, tenant_id: int, file_asset_id: int) -> None:
        if self.settings.search_backend.lower() == "db":
            return
        metadata = await self.session.scalar(
            select(ContentMetadata).where(
                ContentMetadata.tenant_id == tenant_id,
                ContentMetadata.file_asset_id == file_asset_id,
            )
        )
        asset = await self.session.get(FileAsset, file_asset_id)
        if asset is None or int(asset.tenant_id) != int(tenant_id):
            raise ValueError("File asset not found")
        self.search_client.upsert_documents(
            documents=[
                {
                    "id": f"file_asset:{tenant_id}:{file_asset_id}",
                    "tenant_id": tenant_id,
                    "entity_type": "file_asset",
                    "entity_id": file_asset_id,
                    "title": metadata.title if metadata and metadata.title else asset.filename,
                    "description": metadata.description if metadata and metadata.description else "",
                    "tags": json.loads(metadata.tags_json) if metadata else [],
                    "body": " ".join(
                        item for item in [asset.filename, metadata.description if metadata else ""] if item
                    ),
                    "content_type": asset.content_type,
                    "cdn_url": asset.cdn_url,
                    "object_key": asset.object_key,
                }
            ]
        )
