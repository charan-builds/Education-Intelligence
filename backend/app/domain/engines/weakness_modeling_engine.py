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

        return {
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
