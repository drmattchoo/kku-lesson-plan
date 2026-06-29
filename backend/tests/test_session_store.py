import app.session_store as session_store
from app.session_store import create_session, get_session, update_session


def test_create_and_get_session_round_trips(monkeypatch, tmp_path):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)

    session_id = create_session({"foo": "bar"})

    assert get_session(session_id) == {"foo": "bar"}


def test_get_session_returns_none_for_unknown_id(monkeypatch, tmp_path):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)

    assert get_session("does-not-exist") is None


def test_update_session_overwrites_stored_data(monkeypatch, tmp_path):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)
    session_id = create_session({"foo": "bar"})

    update_session(session_id, {"foo": "baz"})

    assert get_session(session_id) == {"foo": "baz"}
