from app.infrastructure.clients.ai_service_client import AIServiceClient
import asyncio


def test_ai_service_client_compacts_mentor_payload_context():
    client = AIServiceClient(base_url="http://example.com")

    payload = {
        "roadmap_progress": {"completion_rate": 48, "completed_steps": 3, "total_steps": 8, "overdue_steps": 1},
        "user_profile": {"preferred_learning_style": "practice_focused", "learning_speed": 21.5, "display_name": "Learner"},
        "weak_topics": [
            {"topic_id": 1, "topic_name": "A", "score": 45},
            {"topic_id": 2, "topic_name": "B", "score": 50},
            {"topic_id": 3, "topic_name": "C", "score": 52},
            {"topic_id": 4, "topic_name": "D", "score": 54},
            {"topic_id": 5, "topic_name": "E", "score": 56},
        ],
        "strong_topics": [
            {"topic_id": 9, "topic_name": "X", "score": 90},
            {"topic_id": 10, "topic_name": "Y", "score": 88},
            {"topic_id": 11, "topic_name": "Z", "score": 86},
        ],
        "recent_activity": [{"event_type": "study", "topic_name": f"Topic {index}", "minutes": index} for index in range(6)],
        "memory_profile": {
            "learner_summary": "x" * 500,
            "past_mistakes": [f"mistake-{index}" for index in range(5)],
            "improvement_signals": [f"signal-{index}" for index in range(5)],
            "last_session_summary": "y" * 500,
        },
        "cognitive_model": {
            "confusion_level": "medium",
            "teaching_style": "z" * 300,
            "adaptive_actions": [f"action-{index}" for index in range(5)],
        },
    }

    compacted = client._compact_mentor_context(payload)

    assert len(compacted["weak_topics"]) == 4
    assert len(compacted["strong_topics"]) == 2
    assert len(compacted["recent_activity"]) == 4
    assert len(compacted["memory_profile"]["past_mistakes"]) == 3
    assert len(compacted["cognitive_model"]["adaptive_actions"]) == 3
    assert len(compacted["memory_profile"]["learner_summary"]) <= 240


def test_ai_service_client_compacts_chat_history():
    client = AIServiceClient(base_url="http://example.com")

    history = [{"role": "user", "content": f"message-{index}" * 100} for index in range(6)]

    compacted = client._compact_chat_history(history)

    assert len(compacted) == 4
    assert all(len(item["content"]) <= 320 for item in compacted)


def test_ai_service_client_cache_scope_includes_user_context_version():
    class _Cache:
        async def namespace_version(self, namespace: str) -> int:
            assert namespace == "ai-context:user:7:42"
            return 9

    async def _run():
        client = AIServiceClient(base_url="http://example.com")
        client.cache_service = _Cache()
        scoped = await client._cache_scope_payload(
            endpoint="/ai/mentor-chat",
            payload={"message": "hi"},
            tenant_id=7,
            user_id=42,
        )
        assert scoped["tenant_id"] == 7
        assert scoped["user_id"] == 42
        assert scoped["context_version"] == 9

    asyncio.run(_run())


def test_ai_service_client_contextual_cache_key_changes_when_version_changes():
    client = AIServiceClient(base_url="http://example.com")
    key_one = client._cache_key("/ai/mentor-chat", {"payload": {"message": "hi"}, "tenant_id": 1, "user_id": 2, "context_version": 1})
    key_two = client._cache_key("/ai/mentor-chat", {"payload": {"message": "hi"}, "tenant_id": 1, "user_id": 2, "context_version": 2})
    assert key_one != key_two
