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


def _format_lo_refs(clo_ids: list, clos_by_id: dict) -> str:
    """ผลการเรียนรู้ column: "PLO{x}/CLO{y}" per mapped CLO (one PLO/CLO pair per
    line), or bare "CLO{y}" if that CLO has no ploRefs. e.g. PLO4/CLO2\nPLO6/CLO5."""
    if not clo_ids:
        return "-"
    lines = []
    for clo_id in clo_ids:
        clo = clos_by_id.get(str(clo_id))
        plo_refs = clo.get("ploRefs") if clo else None
        if plo_refs:
            lines.append(f"PLO{','.join(str(p) for p in plo_refs)}/CLO{clo_id}")
        else:
            lines.append(f"CLO{clo_id}")
    return "\n".join(lines)


def _prepare_context(context: dict) -> dict:
    clos_by_id = {str(clo["id"]): clo for clo in context.get("CLOs", [])}
    key_points = [
        {**kp, "cloRefsText": _format_lo_refs(kp.get("cloRefs", []), clos_by_id)}
        for kp in context.get("keyPoints", [])
    ]
    return {**context, "keyPoints": key_points}


def render_lesson_plan(context: dict, output_path: Path) -> Path:
    tpl = DocxTemplate(TEMPLATE_PATH)
    tpl.render(_with_line_breaks(_prepare_context(context)))
    tpl.save(output_path)
    return output_path
