import json
import logging
import redis
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from .db import SessionLocal
from .db.repositories import load_messages as load_messages_db
from .db.repositories import save_messages as save_messages_db


logger = logging.getLogger(__name__)


class RedisSessionManager:
    """
    Manages chat sessions with Redis backend.
    Supports multiple concurrent users with isolated conversations.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.session_ttl = 3600 * 24  # 24 hours

    def _to_serialized(self, messages: List[BaseMessage]) -> List[dict]:
        serialized = []
        for msg in messages:
            serialized.append(
                {
                    "type": "human" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content,
                }
            )
        return serialized

    def _to_messages(self, serialized: List[dict]) -> List[BaseMessage]:
        messages: List[BaseMessage] = []
        for msg in serialized:
            if msg.get("type") == "human":
                messages.append(HumanMessage(content=msg.get("content", "")))
            else:
                messages.append(AIMessage(content=msg.get("content", "")))
        return messages

    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for a session."""
        return f"chat:session:{session_id}"

    def save_messages(self, session_id: str, messages: List[BaseMessage]) -> None:
        """
        Write-through persistence:
        - durable full history in SQL
        - hot cache in Redis with TTL
        """
        serialized = self._to_serialized(messages)

        with SessionLocal() as db:
            save_messages_db(
                db, session_id=session_id, messages=serialized, replace=True
            )
            db.commit()

        key = self._session_key(session_id)
        try:
            self.redis.setex(key, self.session_ttl, json.dumps(serialized))
        except redis.RedisError as exc:
            logger.warning("Redis save failed for session %s: %s", session_id, exc)

    def load_messages(self, session_id: str) -> List[BaseMessage]:
        """
        Read path:
        - Redis hot cache first
        - SQL fallback when cache misses or Redis is unavailable
        """
        key = self._session_key(session_id)
        try:
            data = self.redis.get(key)
            if data is not None:
                serialized = json.loads(data)
                return self._to_messages(serialized)
        except (redis.RedisError, json.JSONDecodeError) as exc:
            logger.warning("Redis load failed for session %s: %s", session_id, exc)

        with SessionLocal() as db:
            serialized = load_messages_db(db, session_id)

        if not serialized:
            return []

        # repopulate Redis hot cache from SQL after fallback
        try:
            self.redis.setex(key, self.session_ttl, json.dumps(serialized))
        except redis.RedisError:
            pass

        return self._to_messages(serialized)

    def clear_session(self, session_id: str) -> None:
        """Delete only Redis hot cache for a session."""
        key = self._session_key(session_id)
        try:
            self.redis.delete(key)
        except redis.RedisError:
            pass

    def extend_session(self, session_id: str) -> None:
        """Reset TTL for an active session."""
        key = self._session_key(session_id)
        try:
            self.redis.expire(key, self.session_ttl)
        except redis.RedisError:
            pass
