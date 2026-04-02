from collections import defaultdict


class PrerequisiteTracer:
    def __init__(self, prerequisites: list[tuple[int, int]]) -> None:
        self.graph: dict[int, list[int]] = defaultdict(list)
        for topic_id, prereq_id in prerequisites:
            self.graph[topic_id].append(prereq_id)

    def trace_all(self, topic_id: int) -> list[int]:
        visited: set[int] = set()

        def dfs(current: int) -> None:
            for prereq in self.graph.get(current, []):
                if prereq not in visited:
                    visited.add(prereq)
                    dfs(prereq)

        dfs(topic_id)
        return list(visited)
