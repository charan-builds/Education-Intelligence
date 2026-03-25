from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings


class KafkaUnavailableError(RuntimeError):
    pass


def _connection_kwargs() -> dict[str, Any]:
    settings = get_settings()
    kwargs: dict[str, Any] = {
        "bootstrap_servers": [item.strip() for item in settings.kafka_bootstrap_servers.split(",") if item.strip()],
        "security_protocol": settings.kafka_security_protocol,
    }
    if settings.kafka_sasl_mechanism:
        kwargs["sasl_mechanism"] = settings.kafka_sasl_mechanism
    if settings.kafka_sasl_username:
        kwargs["sasl_plain_username"] = settings.kafka_sasl_username
    if settings.kafka_sasl_password:
        kwargs["sasl_plain_password"] = settings.kafka_sasl_password
    return kwargs


@dataclass(slots=True)
class KafkaRecord:
    topic: str
    partition: int
    offset: int
    key: bytes | None
    value: bytes


class KafkaProducerClient:
    def __init__(self, producer: Any | None = None):
        if producer is not None:
            self._producer = producer
            return
        try:
            from kafka import KafkaProducer
        except Exception as exc:  # pragma: no cover
            raise KafkaUnavailableError("kafka-python is not installed") from exc
        settings = get_settings()
        self._producer = KafkaProducer(
            client_id=settings.kafka_client_id,
            value_serializer=lambda value: json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            key_serializer=lambda value: value.encode("utf-8") if value is not None else None,
            acks="all",
            **_connection_kwargs(),
        )

    def send(self, *, topic: str, key: str, value: dict, headers: list[tuple[str, bytes]] | None = None) -> None:
        future = self._producer.send(topic, key=key, value=value, headers=headers or [])
        future.get(timeout=10)

    def flush(self) -> None:
        self._producer.flush()


class KafkaConsumerClient:
    def __init__(
        self,
        *,
        topics: list[str],
        group_id: str,
        consumer: Any | None = None,
        enable_auto_commit: bool = False,
    ):
        if consumer is not None:
            self._consumer = consumer
            return
        try:
            from kafka import KafkaConsumer
        except Exception as exc:  # pragma: no cover
            raise KafkaUnavailableError("kafka-python is not installed") from exc
        settings = get_settings()
        self._consumer = KafkaConsumer(
            *topics,
            client_id=settings.kafka_client_id,
            group_id=group_id,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            key_deserializer=lambda value: value.decode("utf-8") if value is not None else None,
            enable_auto_commit=enable_auto_commit,
            auto_offset_reset="earliest",
            max_poll_records=settings.kafka_consumer_batch_size,
            consumer_timeout_ms=settings.kafka_consumer_poll_timeout_ms,
            **_connection_kwargs(),
        )

    def poll(self, timeout_ms: int, max_records: int) -> list[KafkaRecord]:
        items = self._consumer.poll(timeout_ms=timeout_ms, max_records=max_records)
        records: list[KafkaRecord] = []
        for topic_partition, messages in items.items():
            for message in messages:
                records.append(
                    KafkaRecord(
                        topic=message.topic,
                        partition=int(message.partition),
                        offset=int(message.offset),
                        key=message.key.encode("utf-8") if isinstance(message.key, str) else message.key,
                        value=json.dumps(message.value).encode("utf-8"),
                    )
                )
        return records

    def seek(self, topic: str, partition: int, offset: int) -> None:
        from kafka import TopicPartition

        topic_partition = TopicPartition(topic, partition)
        self._consumer.assign([topic_partition])
        self._consumer.seek(topic_partition, offset)

    def close(self) -> None:
        self._consumer.close()
