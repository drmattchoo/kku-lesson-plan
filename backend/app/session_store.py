from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from app.config import REPO_ROOT

SESSIONS_DIR = REPO_ROOT / "sessions"


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def create_session(data: dict) -> str:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session_id = uuid.uuid4().hex
    _session_path(session_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return session_id


def get_session(session_id: str) -> Optional[dict]:
    path = _session_path(session_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def update_session(session_id: str, data: dict) -> None:
    _session_path(session_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
