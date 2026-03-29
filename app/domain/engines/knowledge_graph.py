from collections import defaultdict
from typing import Protocol


class TopicGraphReader(Protocol):
    async def get_prerequisite_edges(self, tenant_id: int | None = None) -> list[tuple[int, int]]: ...


class KnowledgeGraphEngine:
    def __init__(self, topic_repository: TopicGraphReader) -> None:
        self.topic_repository = topic_repository

    async def _build_graph(self, tenant_id: int) -> dict[int, list[int]]:
        edges = await self.topic_repository.get_prerequisite_edges(tenant_id=tenant_id)
        graph: dict[int, list[int]] = defaultdict(list)
        for topic_id, prerequisite_topic_id in edges:
            graph[topic_id].append(prerequisite_topic_id)

        for topic_id in list(graph.keys()):
            graph[topic_id] = sorted(set(graph[topic_id]))
        return graph

    @staticmethod
    def _dependency_depth_map(graph: dict[int, list[int]]) -> dict[int, int]:
        visiting: set[int] = set()
        memo: dict[int, int] = {}

        def depth(current: int) -> int:
            if current in memo:
                return memo[current]
            if current in visiting:
                raise ValueError(f"Circular dependency detected at topic {current}")

            visiting.add(current)
            prerequisites = graph.get(current, [])
            if not prerequisites:
                result = 0
            else:
                result = 1 + max(depth(prerequisite) for prerequisite in prerequisites)
            visiting.remove(current)
            memo[current] = result
            return result

        for topic_id in list(graph.keys()):
            depth(topic_id)
        return memo

    def _dfs_prerequisites(
        self,
        graph: dict[int, list[int]],
        topic_id: int,
    ) -> list[int]:
        visited: set[int] = set()
        visiting: set[int] = set()
        ordered: list[int] = []

        def visit(current: int) -> None:
            if current in visiting:
                raise ValueError(f"Circular dependency detected at topic {current}")
            if current in visited:
                return

            visiting.add(current)
            for prerequisite in graph.get(current, []):
                visit(prerequisite)
                if prerequisite not in ordered:
                    ordered.append(prerequisite)
            visiting.remove(current)
            visited.add(current)

        visit(topic_id)
        return ordered

    async def get_prerequisites(self, topic_id: int, tenant_id: int) -> list[int]:
        graph = await self._build_graph(tenant_id=tenant_id)
        return self._dfs_prerequisites(graph, topic_id)

    async def get_dependency_depth(self, topic_id: int, tenant_id: int) -> int:
        graph = await self._build_graph(tenant_id=tenant_id)
        return self._dependency_depth_map(graph).get(topic_id, 0)

    async def get_dependency_depths(self, topic_ids: list[int], tenant_id: int) -> dict[int, int]:
        graph = await self._build_graph(tenant_id=tenant_id)
        depth_map = self._dependency_depth_map(graph)
        return {int(topic_id): int(depth_map.get(topic_id, 0)) for topic_id in topic_ids}

    async def generate_learning_paths(self, target_topic_ids: list[int], tenant_id: int) -> dict[int, list[int]]:
        graph = await self._build_graph(tenant_id=tenant_id)
        return {
            int(topic_id): self._dfs_prerequisites(graph, int(topic_id)) + [int(topic_id)]
            for topic_id in target_topic_ids
        }

    async def detect_missing_foundations(
        self,
        topic_scores: dict[int, float],
        tenant_id: int,
    ) -> list[int]:
        graph = await self._build_graph(tenant_id=tenant_id)
        weak_threshold = 70.0

        missing_topics: list[int] = []
        for topic_id in sorted(topic_scores.keys()):
            prerequisites = self._dfs_prerequisites(graph, topic_id)
            if any(topic_scores.get(prerequisite, 0.0) < weak_threshold for prerequisite in prerequisites):
                missing_topics.append(topic_id)

        return missing_topics

    async def generate_learning_path(self, target_topic_id: int, tenant_id: int) -> list[int]:
        prerequisites = await self.get_prerequisites(topic_id=target_topic_id, tenant_id=tenant_id)
        return prerequisites + [target_topic_id]
