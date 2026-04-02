from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import NotFoundError
from app.domain.models.roadmap import Roadmap
from app.domain.models.roadmap_step import RoadmapStep
from app.domain.models.skill import Skill
from app.domain.models.topic import Topic
from app.domain.models.topic_prerequisite import TopicPrerequisite
from app.domain.models.topic_score import TopicScore
from app.domain.models.topic_skill import TopicSkill
from app.domain.models.user import User
from app.infrastructure.repositories.tenant_scoping import user_belongs_to_tenant

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
MASTERY_THRESHOLD = 70.0
WEAK_THRESHOLD = 60.0


@dataclass(frozen=True)
class TopicSemanticProfile:
    topic_id: int
    skill_ids: set[int]
    tokens: set[str]
    cluster_key: str


class TopicKnowledgeService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _load_topics(self, tenant_id: int) -> list[Topic]:
        result = await self.session.execute(
            select(Topic).where(Topic.tenant_id == tenant_id).order_by(Topic.id.asc())
        )
        return list(result.scalars().all())

    async def _load_prerequisites(self, tenant_id: int) -> list[tuple[int, int]]:
        result = await self.session.execute(
            select(TopicPrerequisite.topic_id, TopicPrerequisite.prerequisite_topic_id)
            .join(Topic, Topic.id == TopicPrerequisite.topic_id)
            .where(Topic.tenant_id == tenant_id)
        )
        return [(int(topic_id), int(prerequisite_id)) for topic_id, prerequisite_id in result.all()]

    async def _load_topic_skill_rows(self, tenant_id: int) -> list[tuple[int, int, str]]:
        result = await self.session.execute(
            select(TopicSkill.topic_id, Skill.id, Skill.name)
            .join(Topic, Topic.id == TopicSkill.topic_id)
            .join(Skill, Skill.id == TopicSkill.skill_id)
            .where(Topic.tenant_id == tenant_id, Skill.tenant_id == tenant_id)
            .order_by(TopicSkill.topic_id.asc(), Skill.id.asc())
        )
        return [(int(topic_id), int(skill_id), str(skill_name)) for topic_id, skill_id, skill_name in result.all()]

    async def _load_topic_scores(self, tenant_id: int, user_id: int | None) -> dict[int, float]:
        if user_id is None:
            return {}

        result = await self.session.execute(
            select(TopicScore.topic_id, TopicScore.score)
            .where(TopicScore.tenant_id == tenant_id, TopicScore.user_id == user_id)
        )
        return {int(topic_id): round(float(score), 2) for topic_id, score in result.all()}

    async def _load_roadmap_status(self, tenant_id: int, user_id: int | None) -> dict[int, str]:
        if user_id is None:
            return {}

        result = await self.session.execute(
            select(RoadmapStep.topic_id, RoadmapStep.progress_status)
            .join(Roadmap, Roadmap.id == RoadmapStep.roadmap_id)
            .where(Roadmap.user_id == user_id, Roadmap.user.has(user_belongs_to_tenant(User, tenant_id)))
        )
        status_by_topic: dict[int, str] = {}
        for topic_id, progress_status in result.all():
            status_by_topic[int(topic_id)] = str(progress_status)
        return status_by_topic

    @staticmethod
    def _build_adjacency(edges: list[tuple[int, int]]) -> tuple[dict[int, list[int]], dict[int, list[int]]]:
        prerequisites_by_topic: dict[int, list[int]] = defaultdict(list)
        dependents_by_topic: dict[int, list[int]] = defaultdict(list)
        for topic_id, prerequisite_id in edges:
            prerequisites_by_topic[topic_id].append(prerequisite_id)
            dependents_by_topic[prerequisite_id].append(topic_id)
        for mapping in (prerequisites_by_topic, dependents_by_topic):
            for topic_id in list(mapping.keys()):
                mapping[topic_id] = sorted(set(mapping[topic_id]))
        return prerequisites_by_topic, dependents_by_topic

    @staticmethod
    def _tokenize(*parts: str | None) -> set[str]:
        tokens: set[str] = set()
        for part in parts:
            if not part:
                continue
            tokens.update(TOKEN_PATTERN.findall(part.lower()))
        return tokens

    def _build_semantic_profiles(
        self,
        topics: list[Topic],
        topic_skill_rows: list[tuple[int, int, str]],
    ) -> dict[int, TopicSemanticProfile]:
        skills_by_topic: dict[int, set[int]] = defaultdict(set)
        skill_names_by_topic: dict[int, list[str]] = defaultdict(list)
        for topic_id, skill_id, skill_name in topic_skill_rows:
            skills_by_topic[topic_id].add(skill_id)
            skill_names_by_topic[topic_id].append(skill_name)

        profiles: dict[int, TopicSemanticProfile] = {}
        for topic in topics:
            skill_names = sorted(skill_names_by_topic.get(int(topic.id), []))
            skill_ids = skills_by_topic.get(int(topic.id), set())
            tokens = self._tokenize(topic.name, topic.description, " ".join(skill_names))
            cluster_key = skill_names[0] if skill_names else (sorted(tokens)[0] if tokens else "general")
            profiles[int(topic.id)] = TopicSemanticProfile(
                topic_id=int(topic.id),
                skill_ids=set(skill_ids),
                tokens=tokens,
                cluster_key=cluster_key,
            )
        return profiles

    @staticmethod
    def _is_completed(topic_id: int, topic_scores: dict[int, float], roadmap_status: dict[int, str]) -> bool:
        progress = str(roadmap_status.get(topic_id, "pending")).lower()
        score = float(topic_scores.get(topic_id, 0.0))
        return progress == "completed" or score >= 85.0

    @staticmethod
    def _is_locked(topic_scores: dict[int, float], prerequisites: list[int]) -> bool:
        return bool(prerequisites) and not all(float(topic_scores.get(item, 0.0)) >= MASTERY_THRESHOLD for item in prerequisites)

    @staticmethod
    def _is_weak(topic_id: int, topic_scores: dict[int, float], roadmap_status: dict[int, str], prerequisites: list[int]) -> bool:
        if TopicKnowledgeService._is_completed(topic_id, topic_scores, roadmap_status):
            return False
        if TopicKnowledgeService._is_locked(topic_scores, prerequisites):
            return False
        score = float(topic_scores.get(topic_id, 0.0))
        return 0.0 < score < WEAK_THRESHOLD

    @staticmethod
    def _topic_status(topic_id: int, topic_scores: dict[int, float], roadmap_status: dict[int, str], prerequisites: list[int]) -> str:
        progress = str(roadmap_status.get(topic_id, "pending")).lower()
        if TopicKnowledgeService._is_completed(topic_id, topic_scores, roadmap_status):
            return "completed"
        if progress == "in_progress":
            return "in_progress"
        if TopicKnowledgeService._is_locked(topic_scores, prerequisites):
            return "locked"
        if TopicKnowledgeService._is_weak(topic_id, topic_scores, roadmap_status, prerequisites):
            return "weak"
        score = float(topic_scores.get(topic_id, 0.0))
        if score >= MASTERY_THRESHOLD:
            return "ready"
        return "unseen"

    @staticmethod
    def _similarity(left: TopicSemanticProfile, right: TopicSemanticProfile) -> float:
        token_union = left.tokens | right.tokens
        token_score = len(left.tokens & right.tokens) / len(token_union) if token_union else 0.0
        skill_union = left.skill_ids | right.skill_ids
        skill_score = len(left.skill_ids & right.skill_ids) / len(skill_union) if skill_union else 0.0
        return round((token_score * 0.45) + (skill_score * 0.55), 4)

    @staticmethod
    def _dependency_chain(topic_id: int, prerequisites_by_topic: dict[int, list[int]]) -> list[int]:
        ordered: list[int] = []
        visited: set[int] = set()
        visiting: set[int] = set()

        def visit(current: int) -> None:
            if current in visiting:
                raise ValueError(f"Circular dependency detected at topic {current}")
            if current in visited:
                return
            visiting.add(current)
            for prerequisite_id in prerequisites_by_topic.get(current, []):
                visit(prerequisite_id)
                if prerequisite_id not in ordered:
                    ordered.append(prerequisite_id)
            visiting.remove(current)
            visited.add(current)

        visit(topic_id)
        return ordered

    @staticmethod
    def _shortest_path(start_topic_id: int, target_topic_id: int, dependents_by_topic: dict[int, list[int]]) -> list[int]:
        if start_topic_id == target_topic_id:
            return [start_topic_id]

        queue: deque[int] = deque([start_topic_id])
        previous: dict[int, int | None] = {start_topic_id: None}

        while queue:
            current = queue.popleft()
            for next_topic_id in dependents_by_topic.get(current, []):
                if next_topic_id in previous:
                    continue
                previous[next_topic_id] = current
                if next_topic_id == target_topic_id:
                    path = [target_topic_id]
                    cursor: int | None = current
                    while cursor is not None:
                        path.append(cursor)
                        cursor = previous[cursor]
                    return list(reversed(path))
                queue.append(next_topic_id)
        return []

    @staticmethod
    def _best_start_topic(
        target_topic_id: int,
        topic_scores: dict[int, float],
        prerequisites_by_topic: dict[int, list[int]],
    ) -> int:
        chain = TopicKnowledgeService._dependency_chain(target_topic_id, prerequisites_by_topic)
        mastered = [topic_id for topic_id in chain if float(topic_scores.get(topic_id, 0.0)) >= MASTERY_THRESHOLD]
        return mastered[-1] if mastered else (chain[0] if chain else target_topic_id)

    @staticmethod
    def _round_similarity(score: float) -> float:
        return round(score * 100.0, 1)

    async def get_graph_snapshot(self, *, tenant_id: int, user_id: int | None = None) -> dict:
        topics = await self._load_topics(tenant_id)
        edges = await self._load_prerequisites(tenant_id)
        topic_skill_rows = await self._load_topic_skill_rows(tenant_id)
        topic_scores = await self._load_topic_scores(tenant_id, user_id)
        roadmap_status = await self._load_roadmap_status(tenant_id, user_id)

        prerequisites_by_topic, _dependents_by_topic = self._build_adjacency(edges)
        profiles = self._build_semantic_profiles(topics, topic_skill_rows)
        skill_names_by_topic: dict[int, list[str]] = defaultdict(list)
        for topic_id, _skill_id, skill_name in topic_skill_rows:
            skill_names_by_topic[topic_id].append(skill_name)

        cluster_counts: dict[str, int] = defaultdict(int)
        for profile in profiles.values():
            cluster_counts[profile.cluster_key] += 1

        nodes = []
        completed_topic_count = 0
        weak_topic_count = 0
        locked_topic_count = 0
        for topic in topics:
            topic_id = int(topic.id)
            profile = profiles[topic_id]
            prerequisites = prerequisites_by_topic.get(topic_id, [])
            score = topic_scores.get(topic_id)
            status = self._topic_status(topic_id, topic_scores, roadmap_status, prerequisites)
            is_completed = self._is_completed(topic_id, topic_scores, roadmap_status)
            is_locked = self._is_locked(topic_scores, prerequisites) and not is_completed
            is_weak = self._is_weak(topic_id, topic_scores, roadmap_status, prerequisites)
            if is_completed:
                completed_topic_count += 1
            if is_weak:
                weak_topic_count += 1
            if is_locked:
                locked_topic_count += 1
            nodes.append(
                {
                    "id": topic_id,
                    "node_type": "topic",
                    "name": topic.name,
                    "description": topic.description,
                    "mastery_score": score,
                    "cluster": profile.cluster_key,
                    "status": status,
                    "is_completed": is_completed,
                    "is_weak": is_weak,
                    "is_locked": is_locked,
                    "skill_names": sorted(skill_names_by_topic.get(topic_id, [])),
                    "prerequisite_count": len(prerequisites),
                }
            )

        skill_nodes = []
        seen_skills: set[int] = set()
        for topic_id, skill_id, skill_name in topic_skill_rows:
            if skill_id in seen_skills:
                continue
            seen_skills.add(skill_id)
            related_scores = [topic_scores.get(mapped_topic_id, 0.0) for mapped_topic_id, mapped_skill_id, _ in topic_skill_rows if mapped_skill_id == skill_id]
            skill_nodes.append(
                {
                    "id": skill_id,
                    "node_type": "skill",
                    "name": skill_name,
                    "description": f"Derived from {sum(1 for mapped_topic_id, mapped_skill_id, _ in topic_skill_rows if mapped_skill_id == skill_id)} mapped topics.",
                    "mastery_score": round(sum(related_scores) / len(related_scores), 2) if related_scores else None,
                    "cluster": "skills",
                    "status": "connected",
                    "is_completed": False,
                    "is_weak": False,
                    "is_locked": False,
                    "skill_names": [skill_name],
                    "prerequisite_count": 0,
                }
            )

        graph_edges = [
            {
                "source_id": prerequisite_id,
                "target_id": topic_id,
                "edge_type": "prerequisite",
                "strength": 1.0,
            }
            for topic_id, prerequisite_id in edges
        ]
        graph_edges.extend(
            {
                "source_id": topic_id,
                "target_id": skill_id,
                "edge_type": "maps_to_skill",
                "strength": 0.8,
            }
            for topic_id, skill_id, _skill_name in topic_skill_rows
        )

        clusters = [
            {
                "label": cluster,
                "topic_count": count,
            }
            for cluster, count in sorted(cluster_counts.items(), key=lambda item: (-item[1], item[0]))
        ]

        return {
            "nodes": nodes + skill_nodes,
            "edges": graph_edges,
            "clusters": clusters,
            "summary": {
                "topic_count": len(nodes),
                "skill_count": len(skill_nodes),
                "edge_count": len(graph_edges),
                "completed_topic_count": completed_topic_count,
                "weak_topic_count": weak_topic_count,
                "locked_topic_count": locked_topic_count,
            },
        }

    async def explain_reasoning(self, *, tenant_id: int, topic_id: int, user_id: int | None = None) -> dict:
        topics = await self._load_topics(tenant_id)
        topic_by_id = {int(topic.id): topic for topic in topics}
        if topic_id not in topic_by_id:
            raise NotFoundError("Topic not found")

        edges = await self._load_prerequisites(tenant_id)
        topic_skill_rows = await self._load_topic_skill_rows(tenant_id)
        topic_scores = await self._load_topic_scores(tenant_id, user_id)
        roadmap_status = await self._load_roadmap_status(tenant_id, user_id)

        prerequisites_by_topic, dependents_by_topic = self._build_adjacency(edges)
        profiles = self._build_semantic_profiles(topics, topic_skill_rows)
        dependency_chain = self._dependency_chain(topic_id, prerequisites_by_topic)

        missing_foundations = [
            prerequisite_id
            for prerequisite_id in dependency_chain
            if float(topic_scores.get(prerequisite_id, 0.0)) < MASTERY_THRESHOLD
            and str(roadmap_status.get(prerequisite_id, "pending")).lower() != "completed"
        ]
        inferred_missing = [
            prerequisite_id
            for prerequisite_id in missing_foundations
            if float(topic_scores.get(prerequisite_id, 0.0)) < WEAK_THRESHOLD or prerequisite_id not in topic_scores
        ]

        mastered_topics = sorted(
            topic_id_candidate
            for topic_id_candidate, score in topic_scores.items()
            if float(score) >= MASTERY_THRESHOLD
        )
        start_topic_id = self._best_start_topic(topic_id, topic_scores, prerequisites_by_topic)
        shortest_path = self._shortest_path(start_topic_id, topic_id, dependents_by_topic)
        if not shortest_path:
            shortest_path = [*dependency_chain, topic_id]

        similar_topics = []
        current_profile = profiles[topic_id]
        for other_topic_id, other_profile in profiles.items():
            if other_topic_id == topic_id:
                continue
            score = self._similarity(current_profile, other_profile)
            if score <= 0:
                continue
            similar_topics.append(
                {
                    "topic_id": other_topic_id,
                    "topic_name": topic_by_id[other_topic_id].name,
                    "similarity_percent": self._round_similarity(score),
                    "cluster": other_profile.cluster_key,
                    "mastery_score": topic_scores.get(other_topic_id),
                }
            )
        similar_topics.sort(key=lambda item: (-float(item["similarity_percent"]), int(item["topic_id"])))

        recommended_next = []
        for candidate_topic in topics:
            candidate_id = int(candidate_topic.id)
            if candidate_id == topic_id:
                continue
            prerequisite_ids = prerequisites_by_topic.get(candidate_id, [])
            if candidate_id in mastered_topics:
                continue
            if prerequisite_ids and not all(item in mastered_topics for item in prerequisite_ids):
                continue
            semantic_lift = self._similarity(current_profile, profiles[candidate_id])
            readiness = min(
                100.0,
                max(
                    25.0,
                    55.0
                    + (semantic_lift * 30.0)
                    + (15.0 if candidate_id in dependents_by_topic.get(topic_id, []) else 0.0)
                    + (10.0 if not prerequisite_ids else 0.0),
                ),
            )
            recommended_next.append(
                {
                    "topic_id": candidate_id,
                    "topic_name": candidate_topic.name,
                    "reason": (
                        "Unlocks directly from the current topic."
                        if candidate_id in dependents_by_topic.get(topic_id, [])
                        else "Prerequisites are satisfied and the topic is semantically adjacent."
                    ),
                    "readiness_percent": round(readiness, 1),
                }
            )
        recommended_next.sort(key=lambda item: (-float(item["readiness_percent"]), int(item["topic_id"])))

        return {
            "target_topic_id": topic_id,
            "target_topic_name": topic_by_id[topic_id].name,
            "dependency_resolution": [
                {
                    "topic_id": prerequisite_id,
                    "topic_name": topic_by_id[prerequisite_id].name,
                    "mastery_score": topic_scores.get(prerequisite_id),
                    "status": self._topic_status(
                        prerequisite_id,
                        topic_scores,
                        roadmap_status,
                        prerequisites_by_topic.get(prerequisite_id, []),
                    ),
                }
                for prerequisite_id in dependency_chain
            ],
            "shortest_learning_path": [
                {
                    "topic_id": path_topic_id,
                    "topic_name": topic_by_id[path_topic_id].name,
                    "mastery_score": topic_scores.get(path_topic_id),
                    "status": self._topic_status(
                        path_topic_id,
                        topic_scores,
                        roadmap_status,
                        prerequisites_by_topic.get(path_topic_id, []),
                    ),
                }
                for path_topic_id in shortest_path
            ],
            "missing_foundations": [
                {
                    "topic_id": missing_topic_id,
                    "topic_name": topic_by_id[missing_topic_id].name,
                    "mastery_score": topic_scores.get(missing_topic_id),
                    "status": self._topic_status(
                        missing_topic_id,
                        topic_scores,
                        roadmap_status,
                        prerequisites_by_topic.get(missing_topic_id, []),
                    ),
                }
                for missing_topic_id in missing_foundations
            ],
            "inferred_missing_topics": [
                {
                    "topic_id": inferred_topic_id,
                    "topic_name": topic_by_id[inferred_topic_id].name,
                    "mastery_score": topic_scores.get(inferred_topic_id),
                    "status": self._topic_status(
                        inferred_topic_id,
                        topic_scores,
                        roadmap_status,
                        prerequisites_by_topic.get(inferred_topic_id, []),
                    ),
                }
                for inferred_topic_id in inferred_missing
            ],
            "similar_topics": similar_topics[:5],
            "clusters": sorted({profiles[item].cluster_key for item in [topic_id, *dependency_chain]}),
            "recommended_next_topics": recommended_next[:5],
            "readiness_percent": round(
                max(
                    0.0,
                    min(
                        100.0,
                        (float(topic_scores.get(topic_id, 0.0)) * 0.45)
                        + ((1 - (len(missing_foundations) / max(len(dependency_chain), 1))) * 35.0)
                        + (20.0 if not inferred_missing else 0.0),
                    ),
                ),
                1,
            ),
        }
