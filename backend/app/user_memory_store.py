"""SQL-backed store for users, preferences, and session metadata."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .db import SessionLocal
from .db.repositories import (
    attach_session as repo_attach_session,
    get_or_create_user as repo_get_or_create_user,
    get_session_owner,
    get_user_preferences,
    list_sessions_for_user,
    save_user_preferences,
    touch_session as repo_touch_session,
    update_session_summary as repo_update_session_summary,
)


class UserMemoryStore:
    """Defined API for per-user and per-session SQL DB (SQLAlchemy)."""

    def get_or_create_user(self, user_id: int) -> Dict[str, Any]:
        with SessionLocal() as db:
            user = repo_get_or_create_user(db, user_id)
            db.commit()
            return {
                "user_id": user.id,
                "created_at": user.created_at.isoformat(),
            }

    def list_users(self) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            from .db.models import User

            users = db.query(User).order_by(User.id.asc()).all()
            return [
                {
                    "user_id": user.id,
                    "created_at": user.created_at.isoformat(),
                }
                for user in users
            ]

    def start_session(self, user_id: int) -> str:
        from uuid import uuid4

        session_id = str(uuid4())
        self.attach_session(user_id=user_id, session_id=session_id)
        return session_id

    def attach_session(self, user_id: int, session_id: str) -> None:
        with SessionLocal() as db:
            repo_attach_session(db, user_id=user_id, session_id=session_id)
            db.commit()

    def get_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            return list_sessions_for_user(db, user_id)

    def get_user_for_session(self, session_id: str) -> Optional[int]:
        with SessionLocal() as db:
            return get_session_owner(db, session_id)

    def touch_session(self, session_id: str) -> None:
        with SessionLocal() as db:
            repo_touch_session(db, session_id)
            db.commit()

    def update_session_summary(self, session_id: str, summary: str) -> None:
        with SessionLocal() as db:
            repo_update_session_summary(db, session_id, summary)
            db.commit()

    def get_preferences(self, user_id: int) -> Dict[str, Any]:
        with SessionLocal() as db:
            return get_user_preferences(db, user_id)

    def save_preferences(self, user_id: int, prefs: Dict[str, Any]) -> Dict[str, Any]:
        with SessionLocal() as db:
            saved = save_user_preferences(db, user_id, prefs)
            db.commit()
            return saved

    def merge_preference_summary(self, user_id: int, updates: Dict[str, Any]) -> None:
        current = self.get_preferences(user_id)

        list_fields = {"dietary_restrictions", "disliked_ingredients", "saved_recipes"}
        for field, value in updates.items():
            if field not in current:
                continue
            if field in list_fields and isinstance(value, list):
                combined = current.get(field, []) + value
                deduped: List[Any] = []
                seen = set()
                for item in combined:
                    key = repr(item)
                    if key in seen:
                        continue
                    seen.add(key)
                    deduped.append(item)
                current[field] = deduped
            else:
                current[field] = value

        self.save_preferences(user_id, current)
