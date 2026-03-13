import asyncio

import pytest

from app.application.services.graph_index_service import GraphIndexService


class _Topic:
    def __init__(self, topic_id: int, graph_path: str | None = None):
        self.id = topic_id
        self.graph_path = graph_path


class _TopicRepo:
    def __init__(self):
        self.topics = {
            1: _Topic(1),
            2: _Topic(2),
            3: _Topic(3),
            4: _Topic(4),
        }
        self.edges = [(2, 1), (3, 2), (4, 2)]

    async def list_topics(self):
        return [self.topics[k] for k in sorted(self.topics)]

    async def get_prerequisite_edges(self, tenant_id=None):
        return list(self.edges)

    async def update_topic_index(self, topic_id, depth, graph_path):
        topic = self.topics[topic_id]
        topic.depth = depth
        topic.graph_path = graph_path

    async def get_topic(self, topic_id):
        return self.topics.get(topic_id)

    async def list_topics_by_graph_prefix(self, graph_prefix):
        prefix = f"{graph_prefix}/"
        matched = [topic for topic in self.topics.values() if topic.graph_path and topic.graph_path.startswith(prefix)]
        matched.sort(key=lambda t: (getattr(t, "depth", 0), t.id))
        return matched


def test_build_graph_index_sets_depth_and_path_deterministically():
    async def _run():
        repo = _TopicRepo()
        service = GraphIndexService(repo)
        index = await service.build_graph_index()
        assert index[1]["depth"] == 0
        assert index[2]["graph_path"] == "/1/2"
        assert index[3]["graph_path"] == "/1/2/3"
        assert index[4]["graph_path"] == "/1/2/4"

    asyncio.run(_run())


def test_get_descendants_and_ancestors():
    async def _run():
        repo = _TopicRepo()
        service = GraphIndexService(repo)
        await service.build_graph_index()

        descendants = await service.get_descendants(2)
        ancestors = await service.get_ancestors(4)

        assert descendants == [3, 4]
        assert ancestors == [1, 2]

    asyncio.run(_run())


def test_cycle_detection():
    async def _run():
        repo = _TopicRepo()
        repo.edges = [(1, 2), (2, 1)]
        service = GraphIndexService(repo)
        with pytest.raises(ValueError, match="Circular dependency"):
            await service.build_graph_index()

    asyncio.run(_run())
