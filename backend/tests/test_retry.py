import json

import pytest
from pydantic import ValidationError

from app.retry import call_with_retry


def test_call_with_retry_succeeds_on_first_try():
    calls = []

    def fn():
        calls.append(1)
        return "ok"

    assert call_with_retry(fn) == "ok"
    assert len(calls) == 1


def test_call_with_retry_recovers_after_one_failure():
    attempts = {"n": 0}

    def fn():
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise json.JSONDecodeError("bad json", "doc", 0)
        return "recovered"

    assert call_with_retry(fn) == "recovered"
    assert attempts["n"] == 2


def test_call_with_retry_raises_after_exhausting_retries():
    attempts = {"n": 0}

    def fn():
        attempts["n"] += 1
        raise json.JSONDecodeError("always bad", "doc", 0)

    with pytest.raises(json.JSONDecodeError):
        call_with_retry(fn)
    assert attempts["n"] == 2  # 1 initial + 1 retry, never more


def test_call_with_retry_does_not_swallow_other_exceptions():
    def fn():
        raise RuntimeError("not retryable")

    with pytest.raises(RuntimeError):
        call_with_retry(fn)
