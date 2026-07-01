from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import app.auth as auth_module
import app.main as main_module
import app.session_store as session_store
from app.main import app
from app.schemas import LectureOutline

COURSE = {
    "courseCode": "MD672305",
    "courseName": "Physiology for Dental Students",
    "PLOs": [],
    "CLOs": [{"id": "1", "text": "x", "ploRefs": []}],
    "lectures": [
        {"id": "4", "week": "1", "topic": "สรีรวิทยาระบบประสาท", "name": "สรีรวิทยาระบบประสาท",
         "durationMin": 120, "cloRefs": ["1"]},
    ],
}

FAKE_OUTLINE = LectureOutline(
    lectureId="4",
    totalDurationMin=120,
    keyPoints=[
        {
            "seq": 1, "title": "ภาพรวม", "objective": "อธิบายภาพรวมได้",
            "content": "1. หัวข้อย่อย", "durationMin": 60, "teachingMethod": "lecture",
            "cloRefs": ["1"], "materials": "สไลด์", "assessment": "ถาม-ตอบ",
        },
        {
            "seq": 2, "title": "สรุป", "objective": "สรุปได้",
            "content": "1. สรุปประเด็น", "durationMin": 60, "teachingMethod": "quiz",
            "cloRefs": ["1"], "materials": "-", "assessment": "Quiz",
        },
    ],
)


def _logged_in_client(monkeypatch, tmp_path, email="instructor@kku.ac.th"):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)
    token = {"userinfo": {"email": email, "email_verified": True, "name": "Test"}}
    monkeypatch.setattr(
        auth_module.oauth.google, "authorize_access_token", AsyncMock(return_value=token)
    )
    client = TestClient(app)
    client.get("/auth/callback", follow_redirects=False)
    return client


def _session_with_course(client):
    resp = client.post("/api/session", json={"name": "x", "title": "x"})
    sid = resp.json()["sessionId"]
    session = session_store.get_session(sid)
    session["course"] = COURSE
    session_store.update_session(sid, session)
    return sid


def test_create_outline_returns_draft_and_persists_in_session(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _session_with_course(client)
    monkeypatch.setattr(main_module, "generate_outline", lambda lecture, clos, grounding=None, provider=None: FAKE_OUTLINE)

    resp = client.post("/api/outline", json={"sid": sid, "lectureId": "4"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["lectureId"] == "4"
    assert body["totalDurationMin"] == 120
    assert len(body["keyPoints"]) == 2

    stored = session_store.get_session(sid)
    assert stored["outlines"]["4"]["totalDurationMin"] == 120


def test_create_outline_404_when_lecture_not_in_course(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _session_with_course(client)
    monkeypatch.setattr(main_module, "generate_outline", lambda lecture, clos, grounding=None, provider=None: FAKE_OUTLINE)

    resp = client.post("/api/outline", json={"sid": sid, "lectureId": "does-not-exist"})

    assert resp.status_code == 404


def test_create_outline_surfaces_502_when_generation_persistently_fails(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path, email="outline-fail@kku.ac.th")
    sid = _session_with_course(client)

    def always_broken(lecture, clos, grounding=None, provider=None):
        raise KeyError("keyPoints")

    monkeypatch.setattr(main_module, "generate_outline", always_broken)

    resp = client.post("/api/outline", json={"sid": sid, "lectureId": "4"})

    assert resp.status_code == 502


def test_create_outline_requires_login(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)
    anon_client = TestClient(app)

    resp = anon_client.post("/api/outline", json={"sid": "whatever", "lectureId": "4"})

    assert resp.status_code == 401


def test_create_outline_is_rate_limited_per_user(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path, email="ratelimit-outline@kku.ac.th")
    sid = _session_with_course(client)
    monkeypatch.setattr(main_module, "generate_outline", lambda lecture, clos, grounding=None, provider=None: FAKE_OUTLINE)

    for _ in range(10):
        resp = client.post("/api/outline", json={"sid": sid, "lectureId": "4"})
        assert resp.status_code == 200

    resp = client.post("/api/outline", json={"sid": sid, "lectureId": "4"})
    assert resp.status_code == 429


def test_update_outline_recomputes_total_and_persists(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _session_with_course(client)

    edited = FAKE_OUTLINE.model_dump()
    edited["keyPoints"][0]["durationMin"] = 90  # instructor edits the time

    resp = client.put(f"/api/outline/4?sid={sid}", json=edited)

    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "totalMin": 150}

    stored = session_store.get_session(sid)
    assert stored["outlines"]["4"]["keyPoints"][0]["durationMin"] == 90
