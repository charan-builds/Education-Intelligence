from __future__ import annotations

from app.infrastructure.repositories.topic_repository import TopicRepository


class GraphIndexService:
    def __init__(self, topic_repository: TopicRepository):
        self.topic_repository = topic_repository

    async def _load(self, tenant_id: int | None = None) -> tuple[list[int], dict[int, list[int]]]:
        topics = await self.topic_repository.list_topics()
        topic_ids = sorted(topic.id for topic in topics)
        edges = await self.topic_repository.get_prerequisite_edges(tenant_id=tenant_id)

        parents: dict[int, list[int]] = {topic_id: [] for topic_id in topic_ids}
        for topic_id, prerequisite_id in edges:
            if topic_id not in parents:
                parents[topic_id] = []
            parents[topic_id].append(prerequisite_id)

        for topic_id in list(parents.keys()):
            parents[topic_id] = sorted(set(parents[topic_id]))

        return topic_ids, parents

    async def build_graph_index(self, tenant_id: int | None = None) -> dict[int, dict[str, int | str]]:
        topic_ids, parents = await self._load(tenant_id=tenant_id)
        visiting: set[int] = set()
        memo: dict[int, tuple[int, str]] = {}

        def compute(topic_id: int) -> tuple[int, str]:
            if topic_id in memo:
                return memo[topic_id]
            if topic_id in visiting:
                raise ValueError(f"Circular dependency detected at topic {topic_id}")

            visiting.add(topic_id)
            if not parents.get(topic_id):
                depth = 0
                path = f"/{topic_id}"
            else:
                parent_candidates: list[tuple[int, str, int]] = []
                for parent_id in parents[topic_id]:
                    parent_depth, parent_path = compute(parent_id)
                    parent_candidates.append((parent_depth, parent_path, parent_id))

                parent_candidates.sort(key=lambda item: (item[0], item[1], item[2]))
                best_parent_depth, best_parent_path, _ = parent_candidates[0]
                depth = best_parent_depth + 1
                path = f"{best_parent_path}/{topic_id}"

            visiting.remove(topic_id)
            memo[topic_id] = (depth, path)
            return memo[topic_id]

        for topic_id in topic_ids:
            depth, path = compute(topic_id)
            await self.topic_repository.update_topic_index(topic_id=topic_id, depth=depth, graph_path=path)

        return {topic_id: {"depth": memo[topic_id][0], "graph_path": memo[topic_id][1]} for topic_id in topic_ids}

    async def update_graph_index(self, topic_id: int, tenant_id: int | None = None) -> dict[str, int | str]:
        index = await self.build_graph_index(tenant_id=tenant_id)
        if topic_id not in index:
            raise ValueError(f"Topic {topic_id} not found")
        return index[topic_id]

    async def get_descendants(self, topic_id: int) -> list[int]:
        topic = await self.topic_repository.get_topic(topic_id)
        if topic is None:
            return []

        if not topic.graph_path:
            await self.update_graph_index(topic_id)
            topic = await self.topic_repository.get_topic(topic_id)
            if topic is None or not topic.graph_path:
                return []

        descendants = await self.topic_repository.list_topics_by_graph_prefix(topic.graph_path)
        return [item.id for item in descendants]

    async def get_ancestors(self, topic_id: int) -> list[int]:
        topic = await self.topic_repository.get_topic(topic_id)
        if topic is None:
            return []

        if not topic.graph_path:
            await self.update_graph_index(topic_id)
            topic = await self.topic_repository.get_topic(topic_id)
            if topic is None or not topic.graph_path:
                return []

        parts = [int(part) for part in topic.graph_path.strip("/").split("/") if part]
        ancestors = parts[:-1]
        return ancestors
