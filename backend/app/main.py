import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from app.auth import require_kku_user, router as auth_router
from app.config import settings
from app.schemas import InstructorProfile
from app.session_store import create_session
from app.template_binder import render_lesson_plan
from tests.fixtures.dummy_lesson_plan_context import DUMMY_CONTEXT

app = FastAPI(title="แผนการสอน Generator")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, same_site="lax")
app.include_router(auth_router)


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


@app.get("/api/render-proof")
def render_proof(user: dict = Depends(require_kku_user)) -> FileResponse:
    output_path = Path(tempfile.gettempdir()) / "render_proof.docx"
    render_lesson_plan(DUMMY_CONTEXT, output_path)
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="render_proof.docx",
    )
