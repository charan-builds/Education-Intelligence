from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeaknessCluster:
    anchor_topic_id: int
    topic_ids: list[int]
    average_score: float
    severity: str
    missing_foundation_count: int
    label: str


class WeaknessModelingEngine:
    def detect_root_gaps(
        self,
        *,
        topic_scores: dict[int, float],
        prerequisite_map: dict[int, list[int]],
        topic_names: dict[int, str] | None = None,
        weak_threshold: float = 50.0,
    ) -> dict:
        topic_names = topic_names or {}
        weak_topics = [
            {"topic_id": int(topic_id), "score": round(float(score), 2)}
            for topic_id, score in sorted(topic_scores.items(), key=lambda item: item[1])
            if float(score) < weak_threshold
        ]
        weak_topic_ids = {item["topic_id"] for item in weak_topics}

        root_causes: list[dict] = []
        for weak_topic in weak_topics:
            topic_id = int(weak_topic["topic_id"])
            deepest_paths = self._deepest_weak_prerequisite_paths(
                topic_id=topic_id,
                prerequisite_map=prerequisite_map,
                weak_topic_ids=weak_topic_ids,
            )
            seen_root_ids: set[int] = set()
            for path in deepest_paths:
                prerequisite_id = int(path[0])
                if prerequisite_id in seen_root_ids:
                    continue
                seen_root_ids.add(prerequisite_id)
                root_causes.append(
                    {
                        "topic_id": prerequisite_id,
                        "topic": self._topic_label(prerequisite_id, topic_names),
                        "score": round(float(topic_scores.get(prerequisite_id, 0.0)), 2),
                        "affects_topic_id": topic_id,
                        "affects": self._topic_label(topic_id, topic_names),
                        "path_topic_ids": [int(item) for item in path],
                        "path": [self._topic_label(item, topic_names) for item in path],
                        "label": "ROOT GAP",
                    }
                )

        return {
            "weak_topics": weak_topics,
            "root_causes": root_causes,
        }

    @classmethod
    def _deepest_weak_prerequisite_paths(
        cls,
        *,
        topic_id: int,
        prerequisite_map: dict[int, list[int]],
        weak_topic_ids: set[int],
    ) -> list[list[int]]:
        candidates: list[list[int]] = []

        def visit(current_topic_id: int, path_from_affected: list[int], visiting: set[int]) -> None:
            for prerequisite_id in sorted({int(item) for item in prerequisite_map.get(current_topic_id, [])}):
                if prerequisite_id in visiting:
                    continue
                next_path = [*path_from_affected, prerequisite_id]
                if prerequisite_id in weak_topic_ids:
                    candidates.append(list(reversed(next_path)))
                visit(prerequisite_id, next_path, {*visiting, prerequisite_id})

        visit(int(topic_id), [int(topic_id)], {int(topic_id)})
        if not candidates:
            return []

        max_depth = max(len(path) for path in candidates)
        deepest = [path for path in candidates if len(path) == max_depth]
        return sorted(deepest, key=lambda path: (path[0], path))

    @staticmethod
    def _topic_label(topic_id: int, topic_names: dict[int, str]) -> str:
        return str(topic_names.get(int(topic_id)) or f"Topic {int(topic_id)}")

    def analyze(
        self,
        *,
        topic_scores: dict[int, float],
        prerequisite_map: dict[int, list[int]],
        confidence_by_topic: dict[int, float] | None = None,
        retention_by_topic: dict[int, float] | None = None,
    ) -> dict:
        confidence_by_topic = confidence_by_topic or {}
        retention_by_topic = retention_by_topic or {}

        deep_weaknesses: list[dict] = []
        for topic_id, score in sorted(topic_scores.items(), key=lambda item: item[1]):
            prerequisites = prerequisite_map.get(topic_id, [])
            weak_prerequisites = [item for item in prerequisites if topic_scores.get(item, 0.0) < 70.0]
            confidence = float(confidence_by_topic.get(topic_id, 0.6))
            retention = float(retention_by_topic.get(topic_id, max(score / 100.0, 0.1))) * 100.0
            severity_score = (
                (100.0 - float(score)) * 0.5
                + (len(weak_prerequisites) * 12.0)
                + ((1.0 - confidence) * 20.0)
                + max(0.0, 70.0 - retention) * 0.18
            )
            if severity_score < 24:
                continue
            severity = "high" if severity_score >= 48 else "medium" if severity_score >= 32 else "low"
            deep_weaknesses.append(
                {
                    "topic_id": int(topic_id),
                    "score": round(float(score), 2),
                    "confidence": round(confidence, 2),
                    "retention_score": round(retention, 1),
                    "missing_foundations": [int(item) for item in weak_prerequisites],
                    "severity": severity,
                    "severity_score": round(severity_score, 2),
                }
            )

        clusters: list[WeaknessCluster] = []
        visited: set[int] = set()
        weak_topics = {int(topic_id) for topic_id, score in topic_scores.items() if float(score) < 72.0}
        for topic_id in sorted(weak_topics, key=lambda item: topic_scores.get(item, 0.0)):
            if topic_id in visited:
                continue
            neighborhood = [topic_id]
            neighborhood.extend([item for item in prerequisite_map.get(topic_id, []) if item in weak_topics])
            neighborhood.extend(
                [
                    child_topic
                    for child_topic, prerequisites in prerequisite_map.items()
                    if topic_id in prerequisites and child_topic in weak_topics
                ]
            )
            topic_group = sorted(set(neighborhood))
            visited.update(topic_group)
            average_score = sum(float(topic_scores.get(item, 50.0)) for item in topic_group) / max(len(topic_group), 1)
            missing_foundation_count = sum(
                1 for item in topic_group for prerequisite in prerequisite_map.get(item, []) if topic_scores.get(prerequisite, 0.0) < 70.0
            )
            severity = "high" if average_score < 55 or missing_foundation_count >= 3 else "medium" if average_score < 68 else "low"
            clusters.append(
                WeaknessCluster(
                    anchor_topic_id=int(topic_id),
                    topic_ids=[int(item) for item in topic_group],
                    average_score=round(average_score, 2),
                    severity=severity,
                    missing_foundation_count=missing_foundation_count,
                    label=f"Cluster around topic {topic_id}",
                )
            )

        root_gap_analysis = self.detect_root_gaps(
            topic_scores=topic_scores,
            prerequisite_map=prerequisite_map,
        )

        return {
            **root_gap_analysis,
            "deep_weaknesses": deep_weaknesses[:8],
            "weakness_clusters": [
                {
                    "anchor_topic_id": cluster.anchor_topic_id,
                    "topic_ids": cluster.topic_ids,
                    "average_score": cluster.average_score,
                    "severity": cluster.severity,
                    "missing_foundation_count": cluster.missing_foundation_count,
                    "label": cluster.label,
                }
                for cluster in sorted(clusters, key=lambda item: (item.average_score, -len(item.topic_ids)))
            ][:6],
        }
