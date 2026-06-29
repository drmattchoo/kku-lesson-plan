from pathlib import Path

from docxtpl import DocxTemplate

from app.config import REPO_ROOT

TEMPLATE_PATH = REPO_ROOT / "templates" / "kku_lesson_plan.docx"


def render_lesson_plan(context: dict, output_path: Path) -> Path:
    tpl = DocxTemplate(TEMPLATE_PATH)
    tpl.render(context)
    tpl.save(output_path)
    return output_path
