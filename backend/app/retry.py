from __future__ import annotations

import json
from typing import Callable, TypeVar

from pydantic import ValidationError

T = TypeVar("T")

# LLMs occasionally return near-miss JSON (truncated, wrong key, wrong type) — one
# retry is cheap and clears most of those without masking a genuinely broken
# provider/prompt on the second failure.
RETRYABLE_ERRORS = (json.JSONDecodeError, ValidationError, KeyError, TypeError)


def call_with_retry(fn: Callable[[], T], retries: int = 1) -> T:
    last_error = None
    for _ in range(retries + 1):
        try:
            return fn()
        except RETRYABLE_ERRORS as e:
            last_error = e
    raise last_error
