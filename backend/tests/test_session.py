from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import app.auth as auth_module
import app.session_store as session_store
from app.main import app
from app.session_store import get_session

VALID_PROFILE = {
    "name": "ผศ.ดร. สมชาย ใจดี",
    "title": "ผู้ช่วยศาสตราจารย์",
    "department": "สาขาวิชาสรีรวิทยา",
    "faculty": "คณะแพทยศาสตร์",
    "courseCode": "MD672305",
    "courseName": "Physiology for Dental Students",
    "academicYear": "2569",
    "semester": "1",
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
    assert stored["instructorProfile"]["courseCode"] == "MD672305"
    assert stored["ownerEmail"] == "instructor@kku.ac.th"


def test_create_session_requires_login(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)
    anon_client = TestClient(app)

    resp = anon_client.post("/api/session", json=VALID_PROFILE)

    assert resp.status_code == 401


def test_create_session_rejects_incomplete_profile(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)

    resp = client.post("/api/session", json={"name": "no other fields"})

    assert resp.status_code == 422
