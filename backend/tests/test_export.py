import io
import zipfile
from unittest.mock import AsyncMock

import docx
from fastapi.testclient import TestClient

import app.auth as auth_module
import app.session_store as session_store
from app.main import app

COURSE = {
    "courseCode": "MD672305",
    "courseName": "Physiology for Dental Students",
    "PLOs": [{"id": "4", "text": "ตัวอย่าง PLO"}],
    "CLOs": [{"id": "CLO1", "text": "x", "ploRefs": ["4"]}],
    "lectures": [
        {"id": "4", "week": "1", "topic": "สรีรวิทยาระบบประสาท", "name": "x",
         "durationMin": 60, "cloRefs": ["CLO1"]},
        {"id": "5", "week": "1", "topic": "หัวข้อที่สอง", "name": "y",
         "durationMin": 60, "cloRefs": ["CLO1"]},
    ],
}

OUTLINE = {
    "lectureId": "4",
    "totalDurationMin": 60,
    "keyPoints": [
        {"seq": 1, "title": "A", "objective": "objA", "content": "c1",
         "durationMin": 60, "teachingMethod": "lecture", "cloRefs": ["CLO1"],
         "materials": "m", "assessment": "a"},
    ],
}

OUTLINE_2 = {**OUTLINE, "lectureId": "5"}


def _logged_in_client(monkeypatch, tmp_path, email="instructor@kku.ac.th"):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)
    token = {"userinfo": {"email": email, "email_verified": True, "name": "Test"}}
    monkeypatch.setattr(
        auth_module.oauth.google, "authorize_access_token", AsyncMock(return_value=token)
    )
    client = TestClient(app)
    client.get("/auth/callback", follow_redirects=False)
    return client


def _session_with_course_and_outlines(client, outlines):
    resp = client.post(
        "/api/session",
        json={
            "name": "อ.ทดสอบ", "title": "x", "department": "สรีรวิทยา", "faculty": "แพทยศาสตร์",
            "courseCode": "MD1", "courseName": "X", "academicYear": "2569", "semester": "1",
            "learners": "นักศึกษาทันตแพทย์",
        },
    )
    sid = resp.json()["sessionId"]
    session = session_store.get_session(sid)
    session["course"] = COURSE
    session["outlines"] = outlines
    session_store.update_session(sid, session)
    return sid


def test_export_returns_filled_docx(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _session_with_course_and_outlines(client, {"4": OUTLINE})

    resp = client.post(
        "/api/export",
        json={"sid": sid, "lectureId": "4", "sessionDate": "1 ก.ค. 2569", "sessionTime": "09:00-10:00"},
    )

    assert resp.status_code == 200
    doc = docx.Document(io.BytesIO(resp.content))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Physiology for Dental Students" in full_text
    assert "สรีรวิทยาระบบประสาท" in full_text
    assert "นักศึกษาทันตแพทย์" in full_text


def test_export_404_when_outline_not_generated(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _session_with_course_and_outlines(client, {})

    resp = client.post("/api/export", json={"sid": sid, "lectureId": "4"})

    assert resp.status_code == 404


def test_export_requires_login(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)
    anon_client = TestClient(app)

    resp = anon_client.post("/api/export", json={"sid": "whatever", "lectureId": "4"})

    assert resp.status_code == 401


def test_export_batch_returns_zip_with_one_docx_per_lecture(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _session_with_course_and_outlines(client, {"4": OUTLINE, "5": OUTLINE_2})

    resp = client.post(
        "/api/export/batch",
        json={"sid": sid, "lectureIds": ["4", "5"], "sessionDate": "1 ก.ค. 2569", "sessionTime": "09:00-10:00"},
    )

    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = zf.namelist()
    assert len(names) == 2
    assert any("4" in n for n in names)
    assert any("5" in n for n in names)


def test_export_batch_404_if_any_lecture_missing_outline(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _session_with_course_and_outlines(client, {"4": OUTLINE})

    resp = client.post("/api/export/batch", json={"sid": sid, "lectureIds": ["4", "5"]})

    assert resp.status_code == 404
