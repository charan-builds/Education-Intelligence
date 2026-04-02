import asyncio

from app.application.services.topic_knowledge_service import TopicKnowledgeService


class _Topic:
    def __init__(self, topic_id: int, name: str, description: str):
        self.id = topic_id
        self.name = name
        self.description = description


def test_topic_status_flags_cover_completed_weak_and_locked_states():
    service = TopicKnowledgeService(session=None)

    async def _load_topics(_tenant_id):
        return [
            _Topic(1, "Intro", "Foundations"),
            _Topic(2, "Queries", "SQL query practice"),
            _Topic(3, "Joins", "Join tables"),
        ]

    async def _load_prerequisites(_tenant_id):
        return [(2, 1), (3, 2)]

    async def _load_topic_skill_rows(_tenant_id):
        return []

    async def _load_topic_scores(_tenant_id, _user_id):
        return {1: 92.0, 2: 45.0, 3: 0.0}

    async def _load_roadmap_status(_tenant_id, _user_id):
        return {1: "completed", 2: "pending", 3: "pending"}

    service._load_topics = _load_topics  # type: ignore[method-assign]
    service._load_prerequisites = _load_prerequisites  # type: ignore[method-assign]
    service._load_topic_skill_rows = _load_topic_skill_rows  # type: ignore[method-assign]
    service._load_topic_scores = _load_topic_scores  # type: ignore[method-assign]
    service._load_roadmap_status = _load_roadmap_status  # type: ignore[method-assign]

    snapshot = asyncio.run(service.get_graph_snapshot(tenant_id=7, user_id=11))

    nodes = {node["id"]: node for node in snapshot["nodes"] if node["node_type"] == "topic"}

    assert nodes[1]["status"] == "completed"
    assert nodes[1]["is_completed"] is True
    assert nodes[2]["status"] == "weak"
    assert nodes[2]["is_weak"] is True
    assert nodes[3]["status"] == "locked"
    assert nodes[3]["is_locked"] is True
    assert snapshot["summary"]["completed_topic_count"] == 1
    assert snapshot["summary"]["weak_topic_count"] == 1
    assert snapshot["summary"]["locked_topic_count"] == 1
