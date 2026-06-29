from pathlib import Path

import pytest

from app.document_loaders import load_docx_text, load_document_text, load_pptx_text

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


def test_load_pptx_text_extracts_real_slide_deck():
    text = load_pptx_text(FIXTURES / "Autonomic_Nervous_System.pptx")

    assert "Autonomic Nervous System" in text
    assert "Sympathetic Nervous System" in text
    assert "Slide 1:" in text
    # 57 slides in the deck; only blank/decorative ones should be dropped
    assert text.count("Slide ") > 40


def test_load_pptx_text_skips_blank_slides():
    text = load_pptx_text(FIXTURES / "Autonomic_Nervous_System.pptx")
    # no slide block should be just the "Slide N:" header with nothing after it
    for block in text.split("\n\n"):
        lines = block.splitlines()
        assert len(lines) > 1


def test_load_docx_text_extracts_real_course_spec_in_order():
    text = load_docx_text(FIXTURES / "PT.docx")

    assert "แผนการจัดการเรียนรู้" in text
    # the weekly-schedule table's header row should appear, flattened with " | "
    assert "หัวข้อที่สอน" in text
    assert "ผลลัพธ์การเรียนรู้ที่คาดหวังรายหัวข้อ" in text


def test_load_docx_text_dedupes_merged_table_cells():
    text = load_docx_text(FIXTURES / "PT.docx")
    # a horizontally-merged cell's text must appear once per row, not N times in a row
    assert "Course orientation" in text
    for line in text.splitlines():
        if "Course orientation" in line:
            assert line.count("Course orientation") == 1


def test_load_document_text_dispatches_by_extension():
    docx_text = load_document_text(FIXTURES / "PT.docx")
    pptx_text = load_document_text(FIXTURES / "Autonomic_Nervous_System.pptx")

    assert "แผนการจัดการเรียนรู้" in docx_text
    assert "Autonomic Nervous System" in pptx_text


def test_load_document_text_rejects_unsupported_extension():
    with pytest.raises(ValueError):
        load_document_text(FIXTURES / "PS.pdf")
