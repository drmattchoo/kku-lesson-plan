from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List

from fastapi import HTTPException

_calls: Dict[str, List[float]] = defaultdict(list)


def enforce_rate_limit(key: str, *, max_calls: int, window_seconds: float) -> None:
    """Sliding-window limiter, in-process — matches the project's "no real DB
    needed" single-instance scope. Meant to guard the LLM-calling endpoints
    (/api/extract, /api/outline) against accidental double-submits or abuse burning
    through the shared KKU gateway's daily token quota."""
    now = time.monotonic()
    history = _calls[key]
    cutoff = now - window_seconds
    while history and history[0] < cutoff:
        history.pop(0)
    if len(history) >= max_calls:
        raise HTTPException(
            status_code=429, detail="Too many requests — please wait a moment and try again"
        )
    history.append(now)
