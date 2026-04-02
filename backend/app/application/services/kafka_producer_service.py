from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger
from app.events.event_envelope import EventEnvelope
from app.events.kafka_topics import ANALYTICS_TOPIC, LEARNING_EVENTS_TOPIC, NOTIFICATIONS_TOPIC
from app.events.schema_registry import validate_event_envelope
from app.infrastructure.streaming.kafka_client import KafkaProducerClient


class KafkaProducerService:
    def __init__(self, producer: KafkaProducerClient | None = None):
        self.settings = get_settings()
        self.logger = get_logger()
        self.producer = producer or KafkaProducerClient()

    def resolve_topic_name(self, logical_topic: str) -> str:
        mapping = {
            LEARNING_EVENTS_TOPIC: self.settings.kafka_topic_learning_events,
            NOTIFICATIONS_TOPIC: self.settings.kafka_topic_notifications,
            ANALYTICS_TOPIC: self.settings.kafka_topic_analytics,
        }
        return mapping[logical_topic]

    def publish(self, envelope: EventEnvelope) -> None:
        payload = envelope.to_dict()
        validate_event_envelope(payload)
        topic_name = self.resolve_topic_name(envelope.topic)
        self.producer.send(
            topic=topic_name,
            key=envelope.partition_key,
            value=payload,
            headers=[
                ("event_name", envelope.event_name.encode("utf-8")),
                ("schema_version", envelope.schema_version.encode("utf-8")),
                ("message_id", envelope.message_id.encode("utf-8")),
            ],
        )
        self.logger.info(
            "published kafka event",
            extra={
                "log_data": {
                    "topic": topic_name,
                    "event_name": envelope.event_name,
                    "message_id": envelope.message_id,
                    "tenant_id": envelope.tenant_id,
                }
            },
        )
