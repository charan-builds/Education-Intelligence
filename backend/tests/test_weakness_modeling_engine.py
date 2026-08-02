from types import SimpleNamespace

import pytest

from app.application.services.diagnostic.analysis_service import DiagnosticAnalysisService
from app.domain.engines.weakness_modeling_engine import WeaknessModelingEngine


def test_root_gap_detection_traverses_prerequisites_recursively():
    engine = WeaknessModelingEngine()

    result = engine.detect_root_gaps(
        topic_scores={1: 40.0, 2: 45.0, 3: 30.0},
        prerequisite_map={3: [2], 2: [1]},
        topic_names={1: "Statistics", 2: "Linear Algebra", 3: "ML"},
        weak_threshold=50.0,
    )

    ml_root_causes = [item for item in result["root_causes"] if item["affects"] == "ML"]
    assert ml_root_causes == [
        {
            "topic_id": 1,
            "topic": "Statistics",
            "score": 40.0,
            "affects_topic_id": 3,
            "affects": "ML",
            "path_topic_ids": [1, 2, 3],
            "path": ["Statistics", "Linear Algebra", "ML"],
            "label": "ROOT GAP",
        }
    ]


def test_root_gap_detection_finds_deep_gap_through_strong_direct_prerequisite():
    engine = WeaknessModelingEngine()

    result = engine.detect_root_gaps(
        topic_scores={1: 35.0, 2: 90.0, 3: 45.0},
        prerequisite_map={3: [2], 2: [1]},
        topic_names={1: "Statistics", 2: "Linear Algebra", 3: "ML"},
        weak_threshold=50.0,
    )

    assert result["root_causes"] == [
        {
            "topic_id": 1,
            "topic": "Statistics",
            "score": 35.0,
            "affects_topic_id": 3,
            "affects": "ML",
            "path_topic_ids": [1, 2, 3],
            "path": ["Statistics", "Linear Algebra", "ML"],
            "label": "ROOT GAP",
        }
    ]


class _DiagnosticRepository:
    async def get_test_for_user(self, test_id, user_id, tenant_id):
        _ = test_id, user_id, tenant_id
        return SimpleNamespace(id=9)

    async def topic_scores_for_test(self, test_id, user_id, tenant_id):
        _ = test_id, user_id, tenant_id
        return {1: 35.0, 2: 90.0, 3: 45.0}


class _TopicRepository:
    async def get_prerequisite_edges(self, tenant_id):
        _ = tenant_id
        return [(3, 2), (2, 1)]

    async def list_topics_by_ids(self, topic_ids, tenant_id):
        _ = tenant_id
        names = {1: "Statistics", 2: "Linear Algebra", 3: "ML"}
        return [SimpleNamespace(id=topic_id, name=names[topic_id]) for topic_id in topic_ids]


@pytest.mark.asyncio
async def test_diagnostic_gap_service_returns_named_dependency_path():
    service = DiagnosticAnalysisService(
        session=SimpleNamespace(),
        diagnostic_repository=_DiagnosticRepository(),
        topic_repository=_TopicRepository(),
    )

    result = await service.detect_knowledge_gaps(test_id=9, user_id=7, tenant_id=3)

    assert result["root_causes"][0]["topic"] == "Statistics"
    assert result["root_causes"][0]["affects"] == "ML"
    assert result["root_causes"][0]["path"] == ["Statistics", "Linear Algebra", "ML"]
