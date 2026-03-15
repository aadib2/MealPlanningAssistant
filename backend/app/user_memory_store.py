"""
Lightweight JSON-backed store for user profiles, session index, preferences, and session summaries.

JSON schema (data/user_memory.json):
{
    "users": {
        "<user_id>": { "user_id": int, "created_at": str }
    },
    "preferences_by_user": {
        "<user_id>": {
            "dietary_restrictions": [],
            "disliked_ingredients": [],
            "saved_recipes": [],
            "preference_summary": "",
            "diet_types": [],
            "calories_min": 0,
            "calories_max": 2000,
            "total_time": 60
        }
    },
    "sessions_by_user": {
        "<user_id>": [
            {
                "session_id": str,
                "created_at": str,
                "last_active_at": str,
                "summary": str
            }
        ]
    },
    "session_to_user": {
        "<session_id>": int
    }
}
"""

import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

_DEFAULT_PREFS: Dict[str, Any] = {
    "dietary_restrictions": [],
    "disliked_ingredients": [],
    "saved_recipes": [],
    "preference_summary": "",
    "diet_types": [],
    # "calories_min": 0,
    # "calories_max": 2000,
    # "total_time": 60,
}

_EMPTY_STORE: Dict[str, Any] = {
    "users": {},
    "preferences_by_user": {},
    "sessions_by_user": {},
    "session_to_user": {},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserMemoryStore:
    """
    Thread-safe JSON file store.
    All writes go through an atomic temp-file-then-rename pattern
    so a crash never corrupts the data file.
    """

    def __init__(self, path: str = "data/user_memory.json"):
        self._path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            self._save(_EMPTY_STORE)

    # ------------------------------------------------------------------
    # Internal I/O
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, Any]:
        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure all top-level keys exist (forward-compatible)
        for key, default in _EMPTY_STORE.items():
            data.setdefault(key, type(default)())
        return data

    def _save(self, data: Dict[str, Any]) -> None:
        dir_ = os.path.dirname(self._path) or "."
        with tempfile.NamedTemporaryFile(
            "w", dir=dir_, suffix=".tmp", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(data, tmp, indent=2)
            tmp_path = tmp.name
        os.replace(tmp_path, self._path)  # atomic on POSIX

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def get_or_create_user(self, user_id: int) -> Dict[str, Any]:
        """Return existing user entry or create a new one."""
        key = str(user_id)
        with self._lock:
            data = self._load()
            if key not in data["users"]:
                data["users"][key] = {"user_id": user_id, "created_at": _now()}
                self._save(data)
            return data["users"][key]

    def list_users(self) -> List[Dict[str, Any]]:
        with self._lock:
            data = self._load()
        return list(data["users"].values())

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def start_session(self, user_id: int) -> str:
        """Create a new session for user and return its session_id."""
        self.get_or_create_user(user_id)  # ensure user exists
        session_id = str(uuid4())
        now = _now()
        entry = {
            "session_id": session_id,
            "created_at": now,
            "last_active_at": now,
            "summary": "",
        }
        key = str(user_id)
        with self._lock:
            data = self._load()
            data["sessions_by_user"].setdefault(key, []).append(entry)
            data["session_to_user"][session_id] = user_id
            self._save(data)
        return session_id

    def attach_session(self, user_id: int, session_id: str) -> None:
        """
        Attach a client-generated session_id to a user if it is not tracked yet.
        Raises ValueError if the session already belongs to another user.
        """
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")

        self.get_or_create_user(user_id)
        now = _now()
        key = str(user_id)

        with self._lock:
            data = self._load()
            existing_owner = data["session_to_user"].get(session_id)
            if existing_owner is not None and existing_owner != user_id:
                raise ValueError("Session is already owned by another user")

            if existing_owner is None:
                data["session_to_user"][session_id] = user_id
                sessions = data["sessions_by_user"].setdefault(key, [])
                sessions.append(
                    {
                        "session_id": session_id,
                        "created_at": now,
                        "last_active_at": now,
                        "summary": "",
                    }
                )
                self._save(data)

    def get_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Return all sessions for a user, newest first."""
        with self._lock:
            data = self._load()
        sessions = data["sessions_by_user"].get(str(user_id), [])
        return sorted(sessions, key=lambda s: s["last_active_at"], reverse=True)

    def get_user_for_session(self, session_id: str) -> Optional[int]:
        """Reverse lookup: session_id -> user_id."""
        with self._lock:
            data = self._load()
        return data["session_to_user"].get(session_id)

    def touch_session(self, session_id: str) -> None:
        """Update last_active_at for a session."""
        with self._lock:
            data = self._load()
            user_id = data["session_to_user"].get(session_id)
            if user_id is None:
                return
            sessions = data["sessions_by_user"].get(str(user_id), [])
            for s in sessions:
                if s["session_id"] == session_id:
                    s["last_active_at"] = _now()
                    break
            self._save(data)

    def update_session_summary(self, session_id: str, summary: str) -> None:
        """Store a Claude-generated summary on a session."""
        with self._lock:
            data = self._load()
            user_id = data["session_to_user"].get(session_id)
            if user_id is None:
                return
            sessions = data["sessions_by_user"].get(str(user_id), [])
            for s in sessions:
                if s["session_id"] == session_id:
                    s["summary"] = summary
                    s["last_active_at"] = _now()
                    break
            self._save(data)

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------

    def get_preferences(self, user_id: int) -> Dict[str, Any]:
        """Return stored preferences, falling back to defaults."""
        with self._lock:
            data = self._load()
        stored = data["preferences_by_user"].get(str(user_id), {})
        # Merge with defaults so new fields are always present
        return {**_DEFAULT_PREFS, **stored}

    def save_preferences(self, user_id: int, prefs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge prefs dict into stored user preferences and persist.
        Only known keys from _DEFAULT_PREFS are written to avoid storing arbitrary data.
        Returns the saved preferences.
        """
        self.get_or_create_user(user_id)
        allowed_keys = set(_DEFAULT_PREFS.keys())
        filtered = {k: v for k, v in prefs.items() if k in allowed_keys}
        with self._lock:
            data = self._load()
            key = str(user_id)
            existing = data["preferences_by_user"].get(key, dict(_DEFAULT_PREFS))
            existing.update(filtered)
            data["preferences_by_user"][key] = existing
            self._save(data)
        return existing

    def merge_preference_summary(self, user_id: int, updates: Dict[str, Any]) -> None:
        """
        Merge a partial preference update (e.g. from a session summary).
        List fields are unioned, string fields are replaced.
        """
        with self._lock:
            data = self._load()
            key = str(user_id)
            existing = data["preferences_by_user"].get(key, dict(_DEFAULT_PREFS))

            list_fields = {"dietary_restrictions", "disliked_ingredients", "saved_recipes", "diet_types"}
            for field, value in updates.items():
                if field not in _DEFAULT_PREFS:
                    continue
                if field in list_fields and isinstance(value, list):
                    combined = existing.get(field, []) + value
                    # Deduplicate preserving order
                    seen = set()
                    deduped = []
                    for item in combined:
                        key_ = json.dumps(item, sort_keys=True) if isinstance(item, dict) else item
                        if key_ not in seen:
                            seen.add(key_)
                            deduped.append(item)
                    existing[field] = deduped
                else:
                    existing[field] = value

            data["preferences_by_user"][key] = existing
            self._save(data)

    