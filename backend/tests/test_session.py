from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import app.auth as auth_module
import app.session_store as session_store
from app.main import app
from app.session_store import get_session

VALID_PROFILE = {
    "name": "ผศ.ดร. สมชาย ใจดี",
    "title": "ผู้ช่วยศาสตราจารย์",
}


def _logged_in_client(monkeypatch, tmp_path, email="instructor@kku.ac.th"):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)
    token = {"userinfo": {"email": email, "email_verified": True, "name": "Test"}}
    monkeypatch.setattr(
        auth_module.oauth.google, "authorize_access_token", AsyncMock(return_value=token)
    )
    client = TestClient(app)
    client.get("/auth/callback", follow_redirects=False)
    return client


def test_create_session_returns_session_id_and_persists_profile(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)

    resp = client.post("/api/session", json=VALID_PROFILE)

    assert resp.status_code == 200
    session_id = resp.json()["sessionId"]
    assert session_id

    stored = get_session(session_id)
    assert stored["instructorProfile"]["name"] == "ผศ.ดร. สมชาย ใจดี"
    assert stored["ownerEmail"] == "instructor@kku.ac.th"


def test_create_session_requires_login(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)
    anon_client = TestClient(app)

    resp = anon_client.post("/api/session", json=VALID_PROFILE)

    assert resp.status_code == 401


def test_create_session_rejects_incomplete_profile(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)

    resp = client.post("/api/session", json={"name": "no title"})

    assert resp.status_code == 422


def test_get_session_resumes_profile_and_course(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = client.post("/api/session", json=VALID_PROFILE).json()["sessionId"]

    resp = client.get(f"/api/session/{sid}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["instructorProfile"]["name"] == "ผศ.ดร. สมชาย ใจดี"
    assert body["course"] is None
    assert body["outlineLectureIds"] == []


def test_get_session_404_for_other_users_session(monkeypatch, tmp_path):
    owner_client = _logged_in_client(monkeypatch, tmp_path, email="owner@kku.ac.th")
    sid = owner_client.post("/api/session", json=VALID_PROFILE).json()["sessionId"]

    other_client = _logged_in_client(monkeypatch, tmp_path, email="other@kku.ac.th")
    resp = other_client.get(f"/api/session/{sid}")

    assert resp.status_code == 404


def test_get_session_requires_login(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)
    anon_client = TestClient(app)

    resp = anon_client.get("/api/session/whatever")

    assert resp.status_code == 401


def test_update_session_edits_profile_without_losing_course(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = client.post("/api/session", json=VALID_PROFILE).json()["sessionId"]
    session = session_store.get_session(sid)
    session["course"] = {"courseCode": "MD1", "courseName": "X"}
    session_store.update_session(sid, session)

    resp = client.put(f"/api/session/{sid}", json={"name": "ชื่อใหม่", "title": "ตำแหน่งใหม่"})

    assert resp.status_code == 200
    assert resp.json()["sessionId"] == sid
    stored = session_store.get_session(sid)
    assert stored["instructorProfile"]["name"] == "ชื่อใหม่"
    assert stored["course"]["courseCode"] == "MD1"  # untouched


def test_update_session_404_for_unknown_session(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)

    resp = client.put("/api/session/does-not-exist", json=VALID_PROFILE)

    assert resp.status_code == 404


def test_personal_api_key_is_stored_but_never_echoed_back(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = client.post(
        "/api/session", json={**VALID_PROFILE, "llmApiKey": "sk_personal_123"}
    ).json()["sessionId"]

    stored = session_store.get_session(sid)
    assert stored["instructorProfile"]["llmApiKey"] == "sk_personal_123"

    resp = client.get(f"/api/session/{sid}")
    body = resp.json()
    assert body["hasPersonalApiKey"] is True
    assert body["instructorProfile"]["llmApiKey"] == ""


def test_get_session_reports_no_personal_key_when_none_set(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = client.post("/api/session", json=VALID_PROFILE).json()["sessionId"]

    resp = client.get(f"/api/session/{sid}")

    assert resp.json()["hasPersonalApiKey"] is False


def test_update_session_blank_key_preserves_existing_key(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = client.post(
        "/api/session", json={**VALID_PROFILE, "llmApiKey": "sk_original"}
    ).json()["sessionId"]

    resp = client.put(f"/api/session/{sid}", json={"name": "ชื่อใหม่", "title": "x"})

    assert resp.status_code == 200
    stored = session_store.get_session(sid)
    assert stored["instructorProfile"]["llmApiKey"] == "sk_original"
    assert stored["instructorProfile"]["name"] == "ชื่อใหม่"


def test_update_session_nonblank_key_replaces_existing_key(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = client.post(
        "/api/session", json={**VALID_PROFILE, "llmApiKey": "sk_original"}
    ).json()["sessionId"]

    client.put(f"/api/session/{sid}", json={**VALID_PROFILE, "llmApiKey": "sk_replacement"})

    stored = session_store.get_session(sid)
    assert stored["instructorProfile"]["llmApiKey"] == "sk_replacement"
