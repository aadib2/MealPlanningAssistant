from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from .session import SessionLocal
from .repositories import (
    attach_session,
    get_migration_value,
    get_or_create_user,
    save_user_preferences,
    set_migration_value,
    touch_session,
    update_session_summary,
)
from .models import SessionModel


MIGRATION_KEY = "user_memory_json_to_sql_v1"
DEFAULT_PATH = "data/user_memory.json"


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def migrate_user_memory_json(path: str = DEFAULT_PATH) -> dict[str, int]:
    if not os.path.exists(path):
        return {"users": 0, "preferences": 0, "sessions": 0, "skipped": 1}

    with SessionLocal() as db:
        already_done = get_migration_value(db, MIGRATION_KEY)
        if already_done == "done":
            return {"users": 0, "preferences": 0, "sessions": 0, "skipped": 1}

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        users = payload.get("users", {})
        preferences_by_user = payload.get("preferences_by_user", {})
        sessions_by_user = payload.get("sessions_by_user", {})

        users_count = 0
        prefs_count = 0
        sessions_count = 0

        for user_id_str, user_data in users.items():
            try:
                user_id = int(user_data.get("user_id", user_id_str))
            except (TypeError, ValueError):
                continue

            get_or_create_user(db, user_id)
            users_count += 1

        for user_id_str, prefs in preferences_by_user.items():
            try:
                user_id = int(user_id_str)
            except (TypeError, ValueError):
                continue

            save_user_preferences(db, user_id, prefs or {})
            prefs_count += 1

        for user_id_str, sessions in sessions_by_user.items():
            try:
                user_id = int(user_id_str)
            except (TypeError, ValueError):
                continue

            for session_payload in sessions or []:
                session_id = session_payload.get("session_id")
                if not session_id:
                    continue

                attach_session(db, user_id=user_id, session_id=session_id)
                row = db.get(SessionModel, session_id)
                if row is None:
                    continue

                created_at = _parse_dt(session_payload.get("created_at"))
                last_active_at = _parse_dt(session_payload.get("last_active_at"))
                summary = str(session_payload.get("summary", "") or "")

                if created_at:
                    row.created_at = created_at
                if last_active_at:
                    row.last_active_at = last_active_at
                else:
                    touch_session(db, session_id)

                if summary:
                    update_session_summary(db, session_id, summary)

                sessions_count += 1

        set_migration_value(db, MIGRATION_KEY, "done")
        db.commit()

    return {
        "users": users_count,
        "preferences": prefs_count,
        "sessions": sessions_count,
        "skipped": 0,
    }
