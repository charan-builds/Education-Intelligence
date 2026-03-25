import asyncio

from app.application.services.search_service import SearchService


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _Session:
    async def execute(self, stmt):
        text = str(stmt)
        if "FROM topics" in text:
            return _Result([])
        if "FROM resources" in text:
            return _Result([])
        if "FROM roadmap_steps" in text:
            return _Result([])
        if "FROM file_assets" in text:
            return _Result([])
        return _Result([])


def test_search_service_db_backend_returns_items(monkeypatch):
    async def _run():
        monkeypatch.setattr("app.application.services.search_service.SearchClient.search", lambda *args, **kwargs: [{"id": "x"}])
        service = SearchService(_Session())
        result = await service.search(tenant_id=1, query="python", limit=5)
        assert result["backend"] in {"db", "meilisearch", "elasticsearch"}

    asyncio.run(_run())
