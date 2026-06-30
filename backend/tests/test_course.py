from pathlib import Path
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import app.auth as auth_module
import app.main as main_module
import app.session_store as session_store
from app.main import app
from app.schemas import CLO, ExtractedCourse, Lecture

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"

FAKE_COURSE = ExtractedCourse(
    courseCode="MD672308",
    courseName="Physiology for Physical Therapy Students",
    PLOs=[],
    CLOs=[CLO(id="1", text="อธิบายกลไกการทำงานของระบบต่าง ๆ ของร่างกาย", ploRefs=[])],
    lectures=[
        Lecture(id="1", week="1", topic="Course orientation", name="Course orientation",
                durationMin=5, cloRefs=[])
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


def _create_session(client):
    resp = client.post("/api/session", json={"name": "x", "title": "x"})
    return resp.json()["sessionId"]


def test_extract_creates_course_draft_from_real_docx(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _create_session(client)
    monkeypatch.setattr(main_module, "extract_course", lambda text: FAKE_COURSE)

    with open(FIXTURES / "PT.docx", "rb") as f:
        resp = client.post(
            "/api/extract",
            data={"sid": sid},
            files={"spec": ("PT.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )

    assert resp.status_code == 200
    assert resp.json()["courseCode"] == "MD672308"

    stored = session_store.get_session(sid)
    assert stored["course"]["courseCode"] == "MD672308"
    assert "slidesText" not in stored


def test_extract_stores_slides_text_when_provided(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _create_session(client)
    monkeypatch.setattr(main_module, "extract_course", lambda text: FAKE_COURSE)

    with open(FIXTURES / "PT.docx", "rb") as spec_f, \
         open(FIXTURES / "Autonomic_Nervous_System.pptx", "rb") as slides_f:
        resp = client.post(
            "/api/extract",
            data={"sid": sid},
            files={
                "spec": ("PT.docx", spec_f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                "slides": ("ANS.pptx", slides_f, "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
            },
        )

    assert resp.status_code == 200
    stored = session_store.get_session(sid)
    assert "Autonomic Nervous System" in stored["slidesText"]


def test_extract_surfaces_502_when_extraction_persistently_fails(monkeypatch, tmp_path):
    from pydantic import ValidationError

    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _create_session(client)

    def always_broken(text):
        raise ValidationError.from_exception_data("ExtractedCourse", [])

    monkeypatch.setattr(main_module, "extract_course", always_broken)

    with open(FIXTURES / "PT.docx", "rb") as f:
        resp = client.post("/api/extract", data={"sid": sid}, files={"spec": ("PT.docx", f)})

    assert resp.status_code == 502


def test_extract_surfaces_502_on_llm_gateway_api_error(monkeypatch, tmp_path):
    # e.g. the gateway's per-key daily quota is exhausted — a real failure mode
    # hit during manual testing, distinct from a malformed-JSON response, and NOT
    # covered by RETRYABLE_ERRORS (json/pydantic errors only).
    import httpx
    import openai

    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _create_session(client)

    def always_quota_exhausted(text):
        request = httpx.Request("POST", "https://gen.ai.kku.ac.th/api/v1/chat/completions")
        response = httpx.Response(401, request=request, json={"error": "This model reached daily limit."})
        raise openai.AuthenticationError("daily limit", response=response, body=None)

    monkeypatch.setattr(main_module, "extract_course", always_quota_exhausted)

    with open(FIXTURES / "PT.docx", "rb") as f:
        resp = client.post("/api/extract", data={"sid": sid}, files={"spec": ("PT.docx", f)})

    assert resp.status_code == 502
    assert "daily limit" in resp.json()["detail"]


def test_extract_requires_login(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "SESSIONS_DIR", tmp_path)
    anon_client = TestClient(app)

    with open(FIXTURES / "PT.docx", "rb") as f:
        resp = anon_client.post(
            "/api/extract", data={"sid": "whatever"}, files={"spec": ("PT.docx", f)}
        )

    assert resp.status_code == 401


def test_get_course_404_when_not_extracted_yet(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _create_session(client)

    resp = client.get(f"/api/course/{sid}")

    assert resp.status_code == 404


def test_get_course_404_for_other_users_session(monkeypatch, tmp_path):
    owner_client = _logged_in_client(monkeypatch, tmp_path, email="owner@kku.ac.th")
    sid = _create_session(owner_client)

    other_client = _logged_in_client(monkeypatch, tmp_path, email="other@kku.ac.th")
    resp = other_client.get(f"/api/course/{sid}")

    assert resp.status_code == 404


def test_put_course_persists_instructor_corrections(monkeypatch, tmp_path):
    client = _logged_in_client(monkeypatch, tmp_path)
    sid = _create_session(client)
    monkeypatch.setattr(main_module, "extract_course", lambda text: FAKE_COURSE)
    with open(FIXTURES / "PT.docx", "rb") as f:
        client.post("/api/extract", data={"sid": sid}, files={"spec": ("PT.docx", f)})

    corrected = FAKE_COURSE.model_dump()
    corrected["courseName"] = "Corrected by instructor"

    resp = client.put(f"/api/course/{sid}", json=corrected)

    assert resp.status_code == 200
    assert resp.json()["courseName"] == "Corrected by instructor"
    assert session_store.get_session(sid)["course"]["courseName"] == "Corrected by instructor"
