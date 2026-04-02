from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import get_settings


class SearchClientError(RuntimeError):
    pass


class SearchClient:
    def __init__(self):
        self.settings = get_settings()

    def search(self, *, tenant_id: int, query: str, limit: int = 10) -> list[dict]:
        backend = self.settings.search_backend.lower()
        if backend == "meilisearch":
            return self._search_meilisearch(tenant_id=tenant_id, query=query, limit=limit)
        if backend == "elasticsearch":
            return self._search_elasticsearch(tenant_id=tenant_id, query=query, limit=limit)
        raise SearchClientError(f"Unsupported search backend: {backend}")

    def upsert_documents(self, *, documents: list[dict]) -> None:
        if not documents:
            return
        backend = self.settings.search_backend.lower()
        if backend == "meilisearch":
            self._meili_request(
                method="POST",
                path=f"/indexes/{self.settings.meilisearch_index_name}/documents",
                payload=documents,
            )
            return
        if backend == "elasticsearch":
            body = ""
            for item in documents:
                body += json.dumps({"index": {"_index": self.settings.elasticsearch_index_name, "_id": item["id"]}}) + "\n"
                body += json.dumps(item) + "\n"
            self._elastic_request(method="POST", path="/_bulk", raw_body=body.encode("utf-8"), content_type="application/x-ndjson")
            return
        raise SearchClientError(f"Unsupported search backend: {backend}")

    def delete_document(self, *, document_id: str) -> None:
        backend = self.settings.search_backend.lower()
        if backend == "meilisearch":
            self._meili_request(
                method="DELETE",
                path=f"/indexes/{self.settings.meilisearch_index_name}/documents/{document_id}",
            )
            return
        if backend == "elasticsearch":
            self._elastic_request(method="DELETE", path=f"/{self.settings.elasticsearch_index_name}/_doc/{document_id}")
            return
        raise SearchClientError(f"Unsupported search backend: {backend}")

    def _search_meilisearch(self, *, tenant_id: int, query: str, limit: int) -> list[dict]:
        result = self._meili_request(
            method="POST",
            path=f"/indexes/{self.settings.meilisearch_index_name}/search",
            payload={"q": query, "limit": limit, "filter": [f"tenant_id = {tenant_id}"]},
        )
        return list(result.get("hits", []))

    def _search_elasticsearch(self, *, tenant_id: int, query: str, limit: int) -> list[dict]:
        result = self._elastic_request(
            method="GET",
            path=f"/{self.settings.elasticsearch_index_name}/_search",
            payload={
                "size": limit,
                "query": {
                    "bool": {
                        "must": [{"multi_match": {"query": query, "fields": ["title^3", "description^2", "tags", "body"]}}],
                        "filter": [{"term": {"tenant_id": tenant_id}}],
                    }
                },
            },
        )
        return [item.get("_source", {}) | {"_score": item.get("_score")} for item in result.get("hits", {}).get("hits", [])]

    def _meili_request(self, *, method: str, path: str, payload: dict | list | None = None) -> dict:
        return self._request(method=method, url=f"{self.settings.search_url.rstrip('/')}{path}", payload=payload)

    def _elastic_request(
        self,
        *,
        method: str,
        path: str,
        payload: dict | None = None,
        raw_body: bytes | None = None,
        content_type: str = "application/json",
    ) -> dict:
        url = f"{self.settings.search_url.rstrip('/')}{path}"
        return self._request(method=method, url=url, payload=payload, raw_body=raw_body, content_type=content_type)

    def _request(
        self,
        *,
        method: str,
        url: str,
        payload: dict | list | None = None,
        raw_body: bytes | None = None,
        content_type: str = "application/json",
    ) -> dict:
        headers = {"Content-Type": content_type}
        if self.settings.search_api_key:
            headers["Authorization"] = f"Bearer {self.settings.search_api_key}"
            headers["X-Meili-API-Key"] = self.settings.search_api_key
        body = raw_body
        if body is None and payload is not None:
            body = json.dumps(payload).encode("utf-8")
        request = Request(url=url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.settings.search_timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return {}
                return json.loads(raw)
        except (HTTPError, URLError, TimeoutError) as exc:  # pragma: no cover
            raise SearchClientError(str(exc)) from exc
