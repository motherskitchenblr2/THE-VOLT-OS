"""VOLT OS — Event Bus (Redis Streams). Async inter-service communication."""
import redis
import json
import uuid
from datetime import datetime, timezone


class EventBus:
    """Redis Streams-based event bus for inter-service communication."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.stream_prefix = "volt:events:"

    def publish(self, event_type: str, payload: dict, stream: str = None) -> str:
        """Publish an event to the appropriate stream."""
        stream = stream or self._stream_for(event_type)
        event_id = str(uuid.uuid4())
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "payload": json.dumps(payload),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.redis.xadd(f"{self.stream_prefix}{stream}", event, maxlen=10000)
        return event_id

    def subscribe(self, stream: str, group: str, consumer: str, last_id: str = "$"):
        """Subscribe to a stream as a consumer group member."""
        stream_key = f"{self.stream_prefix}{stream}"
        try:
            self.redis.xgroup_create(stream_key, group, id="0", mkstream=True)
        except redis.exceptions.ResponseError:
            pass  # Group already exists
        return self.redis.xreadgroup(group, consumer, {stream_key: ">"}, count=10, block=5000)

    def ack(self, stream: str, group: str, event_id: str):
        """Acknowledge an event has been processed."""
        self.redis.xack(f"{self.stream_prefix}{stream}", group, event_id)

    def get_history(self, stream: str, count: int = 100) -> list[dict]:
        """Get recent events from a stream."""
        stream_key = f"{self.stream_prefix}{stream}"
        entries = self.redis.xrevrange(stream_key, count=count)
        return [self._parse_entry(entry) for entry in entries]

    def _stream_for(self, event_type: str) -> str:
        """Map event type to stream name."""
        prefix = event_type.split(".")[0]
        return prefix

    def _parse_entry(self, entry: tuple) -> dict:
        event_id, fields = entry
        return {
            "id": event_id,
            "event_type": fields.get("event_type"),
            "payload": json.loads(fields.get("payload", "{}")),
            "timestamp": fields.get("timestamp"),
        }
