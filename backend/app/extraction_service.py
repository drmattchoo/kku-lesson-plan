from __future__ import annotations

from typing import Optional

from app.llm import LLMProvider, get_provider
from app.retry import call_with_retry
from app.schemas import ExtractedCourse

SYSTEM_PROMPT = """\
You are extracting structured course data from a Thai university course specification
(มคอ-3 / Course Specification). These documents are messy and inconsistently
formatted — extract ONLY what is explicitly stated. Return STRICT JSON, no markdown
fences, no commentary, matching exactly this shape:

{
  "courseCode": string,
  "courseName": string,
  "PLOs": [{"id": string, "text": string}],
  "CLOs": [{"id": string, "text": string, "ploRefs": [string]}],
  "lectures": [{"id": string, "week": string, "topic": string, "name": string,
                 "durationMin": number or null, "cloRefs": [string]}]
}

Rules:
- courseCode / courseName: from the course number and Thai/English course name fields
  (e.g. "รหัสวิชา/ชุดวิชา", "ภาษาไทย", "ภาษาอังกฤษ").
- PLOs: only if the document states actual PLO id + text. Many course specs have a
  PLO/CLO mapping table that is just headers with empty data rows (it only applies to
  thesis-type courses) — if so, return PLOs as an empty list. Never invent PLOs.
- CLOs: from the course-level learning outcomes section/table (often labeled CLO1,
  CLO2, ...). ploRefs for a CLO: only if the document explicitly maps that CLO to a
  PLO id; otherwise an empty list.
- lectures: one entry per row of the weekly teaching-schedule table (8. แผนการจัดการ
  เรียนรู้ or equivalent). id: sequential "1", "2", ... in table order. week: the
  คาบที่/สัปดาห์ที่ value as written (e.g. "1", "1-2"). topic and name: the หัวข้อที่
  สอน text (keep both Thai and English if both are given; topic and name may be the
  same string). durationMin: convert the time noted next to the week number into
  minutes (e.g. "(55 นาที)" -> 55, "(1 ชม.)" -> 60, "(2 ชม.)" -> 120); null if not
  stated. cloRefs: schedule rows rarely state CLO ids directly — infer the
  best-matching CLO id(s) by comparing the row's topic/expected-outcome text against
  the CLOs you extracted; if nothing clearly matches, return an empty list rather than
  guessing.
"""


def extract_course(document_text: str, provider: Optional[LLMProvider] = None) -> ExtractedCourse:
    provider = provider or get_provider()

    def attempt() -> ExtractedCourse:
        raw = provider.complete_json(SYSTEM_PROMPT, document_text, max_tokens=8000)
        return ExtractedCourse.model_validate(raw)

    return call_with_retry(attempt)
