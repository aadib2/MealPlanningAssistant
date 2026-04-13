from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Message, MigrationState, SessionModel, User, UserPreferences


DEFAULT_PREFERENCES: dict[str, Any] = {
    "dietary_restrictions": [],
    "disliked_ingredients": [],
    "saved_recipes": [],
    "preference_summary": "",
}


def _to_json(value: Any, default: str) -> str:
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return default


def _from_json(value: str, default: Any) -> Any:
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def get_or_create_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id)
        db.add(user)
        db.flush()
    return user


def get_user_preferences(db: Session, user_id: int) -> dict[str, Any]:
    prefs = db.get(UserPreferences, user_id)
    if prefs is None:
        return dict(DEFAULT_PREFERENCES)
    return {
        "dietary_restrictions": _from_json(prefs.dietary_restrictions_json, []),
        "disliked_ingredients": _from_json(prefs.disliked_ingredients_json, []),
        "saved_recipes": _from_json(prefs.saved_recipes_json, []),
        "preference_summary": prefs.preference_summary or "",
    }


def save_user_preferences(
    db: Session, user_id: int, prefs: dict[str, Any]
) -> dict[str, Any]:
    get_or_create_user(db, user_id)
    row = db.get(UserPreferences, user_id)
    if row is None:
        row = UserPreferences(user_id=user_id)
        db.add(row)

    merged = dict(DEFAULT_PREFERENCES)
    merged.update(get_user_preferences(db, user_id))
    merged.update({k: prefs.get(k) for k in DEFAULT_PREFERENCES.keys() if k in prefs})

    # updated DB row based on merged dict
    row.dietary_restrictions_json = _to_json(
        merged.get("dietary_restrictions", []), "[]"
    )
    row.disliked_ingredients_json = _to_json(
        merged.get("disliked_ingredients", []), "[]"
    )
    row.saved_recipes_json = _to_json(merged.get("saved_recipes", []), "[]")
    row.preference_summary = str(merged.get("preference_summary", "") or "")
    # Backward-compatible write for legacy column that may still exist in SQLite.
    if hasattr(row, "diet_types_json"):
        row.diet_types_json = "[]"
    db.flush()
    return merged


def attach_session(db: Session, user_id: int, session_id: str) -> None:
    if not session_id or not isinstance(session_id, str):
        raise ValueError("session_id must be a non-empty string")

    get_or_create_user(db, user_id)
    existing = db.get(SessionModel, session_id)
    if existing is None:
        db.add(SessionModel(id=session_id, user_id=user_id))
        db.flush()
        return
    if existing.user_id != user_id:
        raise ValueError("Session is already owned by another user")


def get_session_owner(db: Session, session_id: str) -> int | None:
    session = db.get(SessionModel, session_id)
    return session.user_id if session else None


def touch_session(db: Session, session_id: str) -> None:
    session = db.get(SessionModel, session_id)
    if session is None:
        return
    session.last_active_at = datetime.now(timezone.utc)
    db.flush()


def update_session_summary(db: Session, session_id: str, summary: str) -> None:
    session = db.get(SessionModel, session_id)
    if session is None:
        return
    session.summary = summary
    session.last_active_at = datetime.now(timezone.utc)
    db.flush()


def list_sessions_for_user(db: Session, user_id: int) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(SessionModel)
        .where(SessionModel.user_id == user_id)
        .order_by(SessionModel.last_active_at.desc())
    ).all()
    return [
        {
            "session_id": row.id,
            "created_at": row.created_at.isoformat(),
            "last_active_at": row.last_active_at.isoformat(),
            "summary": row.summary,
            "title": row.title,
        }
        for row in rows
    ]


def save_messages(
    db: Session,
    session_id: str,
    messages: list[dict[str, Any]],
    *,
    replace: bool = True,
) -> None:
    if replace:
        db.query(Message).filter(Message.session_id == session_id).delete()

    for msg in messages:
        metadata_value = msg.get("metadata", {})
        db.add(
            Message(
                session_id=session_id,
                role=msg.get("type", "ai"),
                content=str(msg.get("content", "")),
                tool_name=msg.get("tool_name"),
                metadata_json=_to_json(metadata_value, "{}"),
            )
        )
    db.flush()


def load_messages(db: Session, session_id: str) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
    ).all()
    return [
        {
            "type": row.role,
            "content": row.content,
            "tool_name": row.tool_name,
            "metadata": _from_json(row.metadata_json, {}),
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


def append_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    *,
    tool_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    db.add(
        Message(
            session_id=session_id,
            role=role,
            content=content,
            tool_name=tool_name,
            metadata_json=_to_json(metadata or {}, "{}"),
        )
    )
    db.flush()


def get_migration_value(db: Session, key: str) -> str | None:
    row = db.get(MigrationState, key)
    return row.value if row else None


def set_migration_value(db: Session, key: str, value: str) -> None:
    row = db.get(MigrationState, key)
    if row is None:
        db.add(MigrationState(key=key, value=value))
    else:
        row.value = value
    db.flush()
