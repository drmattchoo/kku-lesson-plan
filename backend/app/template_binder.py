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


def _strip_prefix(value, prefix: str) -> str:
    s = str(value)
    return s[len(prefix):] if s.upper().startswith(prefix.upper()) else s


def _format_lo_refs(clo_ids: list, clos_by_id: dict) -> str:
    """ผลการเรียนรู้ column: "PLO{x}/CLO{y}" per mapped CLO (one PLO/CLO pair per
    line), or bare "CLO{y}" if that CLO has no ploRefs. e.g. PLO4/CLO2\nPLO6/CLO5.
    IDs may arrive either bare ("1") or already prefixed ("CLO1") depending on
    whether they came from a hand-built fixture or real LLM extraction — normalize
    so we never double up into "CLOCLO1"."""
    if not clo_ids:
        return "-"
    lines = []
    for clo_id in clo_ids:
        clo = clos_by_id.get(str(clo_id))
        plo_refs = clo.get("ploRefs") if clo else None
        clo_label = _strip_prefix(clo_id, "CLO")
        if plo_refs:
            plo_label = ",".join(_strip_prefix(p, "PLO") for p in plo_refs)
            lines.append(f"PLO{plo_label}/CLO{clo_label}")
        else:
            lines.append(f"CLO{clo_label}")
    return "\n".join(lines)


def _prepare_context(context: dict) -> dict:
    clos_by_id = {str(clo["id"]): clo for clo in context.get("CLOs", [])}
    key_points = [
        {
            **kp,
            "cloRefsText": _format_lo_refs(kp.get("cloRefs", []), clos_by_id),
            # the template's content cell uses docxtpl's {{r ... }} run-tag, which
            # ALWAYS strips the enclosing <w:r> — it must always receive a RichText,
            # never a plain string, even when there's no "\n" to turn into a <w:br/>.
            "content": _line_break_richtext(kp.get("content", "")),
        }
        for kp in context.get("keyPoints", [])
    ]
    # the PLO/CLO heading list paragraphs hardcode "PLO{{ plo.id }}"/"CLO{{ clo.id }}"
    # in the template itself — same double-prefix risk as the table column, so the
    # ids fed to those paragraphs must be normalized too.
    plos = [{**plo, "id": _strip_prefix(plo["id"], "PLO")} for plo in context.get("PLOs", [])]
    clos = [{**clo, "id": _strip_prefix(clo["id"], "CLO")} for clo in context.get("CLOs", [])]
    return {**context, "keyPoints": key_points, "PLOs": plos, "CLOs": clos}


def render_lesson_plan(context: dict, output_path: Path) -> Path:
    tpl = DocxTemplate(TEMPLATE_PATH)
    tpl.render(_prepare_context(context))
    tpl.save(output_path)
    return output_path
