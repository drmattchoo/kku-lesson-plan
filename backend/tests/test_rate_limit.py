import pytest
from fastapi import HTTPException

from app.rate_limit import enforce_rate_limit


def test_allows_calls_under_the_limit():
    for _ in range(3):
        enforce_rate_limit("user-a", max_calls=3, window_seconds=60)


def test_blocks_calls_over_the_limit():
    for _ in range(3):
        enforce_rate_limit("user-b", max_calls=3, window_seconds=60)
    with pytest.raises(HTTPException) as exc_info:
        enforce_rate_limit("user-b", max_calls=3, window_seconds=60)
    assert exc_info.value.status_code == 429


def test_limits_are_tracked_independently_per_key():
    for _ in range(3):
        enforce_rate_limit("user-c", max_calls=3, window_seconds=60)
    enforce_rate_limit("user-d", max_calls=3, window_seconds=60)  # different key, unaffected
