from pathlib import Path

from docxtpl import DocxTemplate, RichText

from app.config import REPO_ROOT

TEMPLATE_PATH = REPO_ROOT / "templates" / "kku_lesson_plan.docx"


def _line_break_richtext(text: str) -> RichText:
    rt = RichText()
    for i, line in enumerate(text.split("\n")):
        if i > 0:
            rt.xml += "<w:r><w:br/></w:r>"
        rt.add(line)
    return rt


def _with_line_breaks(value):
    """Table cells (เนื้อหา, etc.) often hold a numbered multi-line list — turn
    any "\n"-joined string into a real Word line break instead of a literal \n."""
    if isinstance(value, str):
        return _line_break_richtext(value) if "\n" in value else value
    if isinstance(value, dict):
        return {k: _with_line_breaks(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_with_line_breaks(v) for v in value]
    return value


def render_lesson_plan(context: dict, output_path: Path) -> Path:
    tpl = DocxTemplate(TEMPLATE_PATH)
    tpl.render(_with_line_breaks(context))
    tpl.save(output_path)
    return output_path
