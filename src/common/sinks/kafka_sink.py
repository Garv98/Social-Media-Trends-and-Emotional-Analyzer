from typing import Any, Dict

try:
    from confluent_kafka import Producer
except Exception as e:  # pragma: no cover
    Producer = None

class KafkaSink:
    """Publish events to a Kafka topic."""

    def __init__(self, bootstrap_servers: str, topic: str, acks: int = 1):
        if Producer is None:
            raise ImportError("confluent-kafka is not installed. Install it to use KafkaSink.")
        self.topic = topic
        self.producer = Producer({
            'bootstrap.servers': bootstrap_servers,
            'acks': acks
        })

    def write(self, event: Dict[str, Any]) -> None:
        import json
        payload = json.dumps(event, ensure_ascii=False)
        self.producer.produce(self.topic, value=payload.encode('utf-8'))

    def flush(self) -> None:
        self.producer.flush()
