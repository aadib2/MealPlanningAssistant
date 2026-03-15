# session-based chat with Redis persistence
import json
import redis
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

class RedisSessionManager:
    """
    Manages chat sessions with Redis backend.
    Supports multiple concurrent users with isolated conversations.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.session_ttl = 3600 * 24  # 24 hours

    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for a session."""
        return f"chat:session:{session_id}"

    def save_messages(self, session_id: str, messages: List[BaseMessage]) -> None:
        """
        Save conversation messages to Redis.
        Serializes messages to JSON for storage.
        """
        key = self._session_key(session_id)

        # Serialize messages to a storable format
        serialized = []
        for msg in messages:
            serialized.append({
                "type": "human" if isinstance(msg, HumanMessage) else "ai",
                "content": msg.content
            })

        # Store with TTL to prevent unbounded growth
        self.redis.setex(key, self.session_ttl, json.dumps(serialized))

    def load_messages(self, session_id: str) -> List[BaseMessage]:
        """
        Load conversation messages from Redis.
        Returns empty list if session does not exist.
        """
        key = self._session_key(session_id)
        data = self.redis.get(key)

        if data is None:
            return []

        # Deserialize messages from JSON
        serialized = json.loads(data)
        messages = []

        for msg in serialized:
            if msg["type"] == "human":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        return messages

    def clear_session(self, session_id: str) -> None:
        """Delete a session and its history."""
        key = self._session_key(session_id)
        self.redis.delete(key)

    def extend_session(self, session_id: str) -> None:
        """Reset TTL for an active session."""
        key = self._session_key(session_id)
        self.redis.expire(key, self.session_ttl)

