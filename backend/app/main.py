import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.config import settings
from app.template_binder import render_lesson_plan
from tests.fixtures.dummy_lesson_plan_context import DUMMY_CONTEXT

app = FastAPI(title="แผนการสอน Generator")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "active_model": settings.active_model}


@app.get("/api/render-proof")
def render_proof() -> FileResponse:
    output_path = Path(tempfile.gettempdir()) / "render_proof.docx"
    render_lesson_plan(DUMMY_CONTEXT, output_path)
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="render_proof.docx",
    )
