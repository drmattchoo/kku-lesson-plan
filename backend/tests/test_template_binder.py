import docx

from app.template_binder import render_lesson_plan
from tests.fixtures.dummy_lesson_plan_context import DUMMY_CONTEXT


def test_render_proof_produces_filled_docx(tmp_path):
    output_path = tmp_path / "render_proof.docx"
    render_lesson_plan(DUMMY_CONTEXT, output_path)

    assert output_path.exists()
    doc = docx.Document(output_path)
    full_text = "\n".join(p.text for p in doc.paragraphs)
    full_text += "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)

    assert "Human Physiology" in full_text
    assert "Autonomic Nervous System" in full_text
    assert "PLO 1 :" in full_text
    assert "CLO 1.2 :" in full_text
    assert "Sympathetic vs Parasympathetic" in full_text
    assert "60" in full_text
    # objective must be a CLO-tied action statement, distinct from the title
    assert "วิเคราะห์ความแตกต่างระหว่าง sympathetic และ parasympathetic ได้" in full_text
    # content is a numbered subtopic list, distinct from title and objective
    assert "Neurotransmitter และ receptor ของแต่ละระบบ" in full_text
