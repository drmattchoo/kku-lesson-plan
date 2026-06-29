from __future__ import annotations

from typing import List, Optional

from app.llm import LLMProvider, get_provider
from app.schemas import CLO, KeyPoint, Lecture, LectureOutline, OutlineGrounding

DEFAULT_DURATION_MIN = 60

SYSTEM_PROMPT = """\
You are drafting a timed teaching outline for ONE lecture in a Thai university
physiology-style course, to be rendered later into a KKU lesson-plan template. Return
STRICT JSON, no markdown fences, no commentary, matching exactly this shape:

{
  "keyPoints": [
    {"seq": int, "title": string, "objective": string, "content": string,
     "durationMin": int, "teachingMethod": "lecture"|"interactive"|"quiz",
     "cloRefs": [string], "materials": string, "assessment": string}
  ]
}

Rules:
- Produce 4-8 key points whose durationMin values sum to approximately the lecture's
  scheduled duration given below; each point should be 5-10 minutes.
- title: a short topic label for that segment.
- objective: a CLO-tied ACTION STATEMENT, never a restatement of title — phrase it
  using the action verb from the CLO(s) you put in this point's cloRefs, applied to
  this point's subject (e.g. CLO "อธิบายกลไก..." + point "ตัวรับ..." ->
  "บอกชนิดของตัวรับ...ได้").
- content: 2-5 numbered subtopics actually covered in that segment, distinct from
  both title and objective.
- teachingMethod: "lecture" for straight delivery, "interactive" for discussion/
  case-work/Q&A, "quiz" for assessed recall (post-test, etc).
- cloRefs: cite ONLY ids from the CLO list given below, best-effort match by topic
  relevance; an empty list if nothing clearly applies — never guess.
- materials: what's used to teach the point (slides, case studies, etc) — if slide
  content is given below, infer from it; otherwise a sensible default.
- assessment: how that point's understanding is checked (ถาม-ตอบ, quiz, post-test).
- The first point is usually a short orientation/objectives segment and the last a
  short summary/Q&A segment, time permitting.
"""


def _build_user_prompt(lecture: Lecture, clos: List[CLO], grounding: Optional[OutlineGrounding]) -> str:
    duration = lecture.durationMin or DEFAULT_DURATION_MIN
    lines = [
        f"Lecture topic: {lecture.name or lecture.topic}",
        f"Scheduled duration: {duration} minutes",
        "",
        "Course-level CLOs this lecture may draw on:",
    ]
    lines += [f"{clo.id}: {clo.text}" for clo in clos] or ["(none given)"]

    if grounding and grounding.slidesText:
        lines += ["", "Lecture slide content (primary source for what's actually taught):", grounding.slidesText]
    if grounding and grounding.brief:
        lines += ["", "Instructor's brief / intent for this lecture:", grounding.brief]
    if not (grounding and (grounding.slidesText or grounding.brief)):
        lines += ["", "No slides or brief provided — derive the outline from the topic and CLOs above using domain knowledge."]

    return "\n".join(lines)


def generate_outline(
    lecture: Lecture,
    clos: List[CLO],
    grounding: Optional[OutlineGrounding] = None,
    provider: Optional[LLMProvider] = None,
) -> LectureOutline:
    provider = provider or get_provider()
    user_prompt = _build_user_prompt(lecture, clos, grounding)
    raw = provider.complete_json(SYSTEM_PROMPT, user_prompt, max_tokens=4000)

    key_points = [KeyPoint.model_validate(kp) for kp in raw["keyPoints"]]
    # trust our own arithmetic over whatever total the model may have stated —
    # M9's "live total" editor is where the instructor reconciles this against the
    # lecture's scheduled time, not a hard gate here.
    total_duration_min = sum(kp.durationMin for kp in key_points)

    return LectureOutline(
        lectureId=lecture.id, totalDurationMin=total_duration_min, keyPoints=key_points
    )
