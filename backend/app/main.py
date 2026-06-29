import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from app.auth import require_kku_user, router as auth_router
from app.config import settings
from app.document_loaders import load_document_text
from app.extraction_service import extract_course
from app.lesson_plan_assembler import build_render_context
from app.outline_service import generate_outline
from app.rate_limit import enforce_rate_limit
from app.schemas import (
    CLO,
    BatchExportRequest,
    ExportRequest,
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
    enforce_rate_limit(f"extract:{user['email']}", max_calls=5, window_seconds=60)
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
    enforce_rate_limit(f"outline:{user['email']}", max_calls=10, window_seconds=60)
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


def _render_lecture_docx(session: dict, lecture_id: str, session_date: str, session_time: str) -> Path:
    course_data = session.get("course")
    if course_data is None:
        raise HTTPException(status_code=404, detail="Course not extracted yet")

    outline_data = session.get("outlines", {}).get(lecture_id)
    if outline_data is None:
        raise HTTPException(status_code=404, detail="Outline not generated yet for this lecture")

    lecture_data = next((l for l in course_data["lectures"] if l["id"] == lecture_id), None)
    if lecture_data is None:
        raise HTTPException(status_code=404, detail="Lecture not found")

    course = ExtractedCourse.model_validate(course_data)
    lecture = Lecture.model_validate(lecture_data)
    outline = LectureOutline.model_validate(outline_data)
    instructor = InstructorProfile.model_validate(session["instructorProfile"])

    ctx = build_render_context(instructor, course, lecture, outline, session_date, session_time)
    output_path = Path(tempfile.mkdtemp()) / f"lesson_plan_{lecture_id}.docx"
    render_lesson_plan(ctx, output_path)
    return output_path


@app.post("/api/export")
def export(req: ExportRequest, user: dict = Depends(require_kku_user)) -> FileResponse:
    session = _owned_session(req.sid, user)
    output_path = _render_lecture_docx(session, req.lectureId, req.sessionDate, req.sessionTime)
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=output_path.name,
    )


@app.post("/api/export/batch")
def export_batch(req: BatchExportRequest, user: dict = Depends(require_kku_user)) -> FileResponse:
    session = _owned_session(req.sid, user)
    zip_path = Path(tempfile.mkdtemp()) / "lesson_plans.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for lecture_id in req.lectureIds:
            docx_path = _render_lecture_docx(session, lecture_id, req.sessionDate, req.sessionTime)
            zf.write(docx_path, arcname=docx_path.name)
    return FileResponse(zip_path, media_type="application/zip", filename="lesson_plans.zip")


@app.get("/api/render-proof")
def render_proof(user: dict = Depends(require_kku_user)) -> FileResponse:
    output_path = Path(tempfile.gettempdir()) / "render_proof.docx"
    render_lesson_plan(DUMMY_CONTEXT, output_path)
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="render_proof.docx",
    )
