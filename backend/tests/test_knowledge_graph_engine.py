import asyncio

import pytest

from app.domain.engines.knowledge_graph import KnowledgeGraphEngine


class _TopicRepo:
    async def get_prerequisite_edges(self, tenant_id=None):
        # 3 <- 2 <- 1, and 4 depends on 2 and 5
        return [
            (3, 2),
            (2, 1),
            (4, 2),
            (4, 5),
        ]


class _CycleRepo:
    async def get_prerequisite_edges(self, tenant_id=None):
        return [(1, 2), (2, 1)]


def test_get_prerequisites_recursive_deterministic():
    async def _run():
        engine = KnowledgeGraphEngine(_TopicRepo())
        prereqs = await engine.get_prerequisites(topic_id=3, tenant_id=10)
        assert prereqs == [1, 2]

    asyncio.run(_run())


def test_get_dependency_depth():
    async def _run():
        engine = KnowledgeGraphEngine(_TopicRepo())
        depth = await engine.get_dependency_depth(topic_id=3, tenant_id=10)
        assert depth == 2

    asyncio.run(_run())


def test_detect_missing_foundations():
    async def _run():
        engine = KnowledgeGraphEngine(_TopicRepo())
        missing = await engine.detect_missing_foundations(
            topic_scores={1: 40.0, 2: 85.0, 3: 90.0, 4: 95.0, 5: 90.0},
            tenant_id=10,
        )
        assert 2 in missing
        assert 3 in missing

    asyncio.run(_run())


def test_generate_learning_path_foundation_first():
    async def _run():
        engine = KnowledgeGraphEngine(_TopicRepo())
        path = await engine.generate_learning_path(target_topic_id=3, tenant_id=10)
        assert path == [1, 2, 3]

    asyncio.run(_run())


def test_cycle_detection():
    async def _run():
        engine = KnowledgeGraphEngine(_CycleRepo())
        with pytest.raises(ValueError, match="Circular dependency"):
            await engine.get_prerequisites(topic_id=1, tenant_id=10)

    asyncio.run(_run())


def test_get_dependency_depths_batches_multiple_topics():
    async def _run():
        engine = KnowledgeGraphEngine(_TopicRepo())
        depth_map = await engine.get_dependency_depths(topic_ids=[2, 3, 4, 99], tenant_id=10)
        assert depth_map == {2: 1, 3: 2, 4: 2, 99: 0}

    asyncio.run(_run())


def test_generate_learning_paths_batches_targets():
    async def _run():
        engine = KnowledgeGraphEngine(_TopicRepo())
        paths = await engine.generate_learning_paths(target_topic_ids=[3, 4], tenant_id=10)
        assert paths[3] == [1, 2, 3]
        assert paths[4] == [1, 2, 5, 4]

    asyncio.run(_run())
