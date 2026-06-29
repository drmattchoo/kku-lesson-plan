import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from app.auth import require_kku_user, router as auth_router
from app.config import settings
from app.document_loaders import load_document_text
from app.extraction_service import extract_course
from app.outline_service import generate_outline
from app.schemas import (
    CLO,
    ExtractedCourse,
    InstructorProfile,
    Lecture,
    LectureOutline,
    OutlineGrounding,
    OutlineRequest,
)
from app.session_store import create_session, get_session, update_session
from app.template_binder import render_lesson_plan
from tests.fixtures.dummy_lesson_plan_context import DUMMY_CONTEXT

app = FastAPI(title="แผนการสอน Generator")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, same_site="lax")
app.include_router(auth_router)


def _owned_session(sid: str, user: dict) -> dict:
    session = get_session(sid)
    if session is None or session.get("ownerEmail") != user["email"]:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _save_upload_to_tmp(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "").suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(upload.file, tmp)
    tmp.close()
    return Path(tmp.name)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "active_model": settings.active_model}


@app.post("/api/session")
def create_instructor_session(
    profile: InstructorProfile, user: dict = Depends(require_kku_user)
) -> dict:
    session_id = create_session(
        {"instructorProfile": profile.model_dump(), "ownerEmail": user["email"]}
    )
    return {"sessionId": session_id}


@app.post("/api/extract")
def extract(
    sid: str = Form(...),
    spec: UploadFile = File(...),
    slides: Optional[UploadFile] = File(None),
    user: dict = Depends(require_kku_user),
) -> dict:
    session = _owned_session(sid, user)

    spec_path = _save_upload_to_tmp(spec)
    try:
        spec_text = load_document_text(spec_path)
    finally:
        spec_path.unlink(missing_ok=True)

    course = extract_course(spec_text)
    session["course"] = course.model_dump()

    if slides is not None and slides.filename:
        slides_path = _save_upload_to_tmp(slides)
        try:
            session["slidesText"] = load_document_text(slides_path)
        finally:
            slides_path.unlink(missing_ok=True)

    update_session(sid, session)
    return session["course"]


@app.get("/api/course/{sid}")
def get_course(sid: str, user: dict = Depends(require_kku_user)) -> dict:
    session = _owned_session(sid, user)
    if "course" not in session:
        raise HTTPException(status_code=404, detail="Course not extracted yet")
    return session["course"]


@app.put("/api/course/{sid}")
def put_course(
    sid: str, corrected: ExtractedCourse, user: dict = Depends(require_kku_user)
) -> dict:
    session = _owned_session(sid, user)
    session["course"] = corrected.model_dump()
    update_session(sid, session)
    return session["course"]


@app.post("/api/outline")
def create_outline(req: OutlineRequest, user: dict = Depends(require_kku_user)) -> dict:
    session = _owned_session(req.sid, user)
    course = session.get("course")
    if course is None:
        raise HTTPException(status_code=404, detail="Course not extracted yet")

    lecture_data = next((l for l in course["lectures"] if l["id"] == req.lectureId), None)
    if lecture_data is None:
        raise HTTPException(status_code=404, detail="Lecture not found")

    lecture = Lecture.model_validate(lecture_data)
    clos = [CLO.model_validate(c) for c in course["CLOs"]]
    grounding = OutlineGrounding(slidesText=session.get("slidesText"), brief=req.brief)

    outline = generate_outline(lecture, clos, grounding=grounding)

    outlines = session.setdefault("outlines", {})
    outlines[req.lectureId] = outline.model_dump()
    update_session(req.sid, session)

    return outline.model_dump()


@app.put("/api/outline/{lid}")
def update_outline(
    lid: str, sid: str, outline: LectureOutline, user: dict = Depends(require_kku_user)
) -> dict:
    session = _owned_session(sid, user)
    outlines = session.setdefault("outlines", {})
    outlines[lid] = outline.model_dump()
    update_session(sid, session)
    total_min = sum(kp.durationMin for kp in outline.keyPoints)
    return {"ok": True, "totalMin": total_min}


@app.get("/api/render-proof")
def render_proof(user: dict = Depends(require_kku_user)) -> FileResponse:
    output_path = Path(tempfile.gettempdir()) / "render_proof.docx"
    render_lesson_plan(DUMMY_CONTEXT, output_path)
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="render_proof.docx",
    )
