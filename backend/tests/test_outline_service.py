from unittest.mock import MagicMock

from app.outline_service import generate_outline
from app.schemas import CLO, Lecture, LectureOutline, OutlineGrounding

LECTURE = Lecture(id="3", week="1", topic="Membrane transport", name="Membrane transport", durationMin=60)
CLOS = [CLO(id="1", text="อธิบายโครงสร้างและหน้าที่ของเยื่อหุ้มเซลล์", ploRefs=[])]

VALID_KEY_POINTS = [
    {
        "seq": 1,
        "title": "ภาพรวมเยื่อหุ้มเซลล์",
        "objective": "อธิบายโครงสร้างพื้นฐานของเยื่อหุ้มเซลล์ได้",
        "content": "1. โครงสร้าง phospholipid bilayer\n2. โปรตีนในเยื่อหุ้มเซลล์",
        "durationMin": 15,
        "teachingMethod": "lecture",
        "cloRefs": ["1"],
        "materials": "สไลด์ PowerPoint",
        "assessment": "ถาม-ตอบในชั้นเรียน",
    },
    {
        "seq": 2,
        "title": "การขนส่งสารแบบ passive/active",
        "objective": "อธิบายกลไกการขนส่งสารผ่านเยื่อหุ้มเซลล์ได้",
        "content": "1. Diffusion และ osmosis\n2. Active transport",
        "durationMin": 45,
        "teachingMethod": "interactive",
        "cloRefs": ["1"],
        "materials": "สไลด์ PowerPoint",
        "assessment": "Quiz สั้นท้ายหัวข้อ",
    },
]


def _provider_returning(key_points):
    provider = MagicMock()
    provider.complete_json.return_value = {"keyPoints": key_points}
    return provider


def test_generate_outline_spec_alone_mode():
    provider = _provider_returning(VALID_KEY_POINTS)

    outline = generate_outline(LECTURE, CLOS, grounding=None, provider=provider)

    assert isinstance(outline, LectureOutline)
    assert outline.lectureId == "3"
    assert outline.totalDurationMin == 60
    assert len(outline.keyPoints) == 2
    assert outline.keyPoints[0].objective != outline.keyPoints[0].title

    _, user_prompt = provider.complete_json.call_args[0]
    assert "No slides or brief provided" in user_prompt
    assert "Membrane transport" in user_prompt
    assert "1: อธิบายโครงสร้างและหน้าที่ของเยื่อหุ้มเซลล์" in user_prompt


def test_generate_outline_uses_slides_grounding_when_present():
    provider = _provider_returning(VALID_KEY_POINTS)
    grounding = OutlineGrounding(slidesText="Slide 1:\nMembrane structure\nSlide 2:\nTransport types")

    generate_outline(LECTURE, CLOS, grounding=grounding, provider=provider)

    _, user_prompt = provider.complete_json.call_args[0]
    assert "Slide 1:" in user_prompt
    assert "primary source" in user_prompt
    assert "No slides or brief provided" not in user_prompt


def test_generate_outline_uses_brief_grounding_when_present():
    provider = _provider_returning(VALID_KEY_POINTS)
    grounding = OutlineGrounding(brief="Focus on clinical correlations for dental students")

    generate_outline(LECTURE, CLOS, grounding=grounding, provider=provider)

    _, user_prompt = provider.complete_json.call_args[0]
    assert "Focus on clinical correlations for dental students" in user_prompt


def test_generate_outline_recomputes_total_from_key_points_not_model():
    # even if a real model response disagreed with itself, our own sum is authoritative
    provider = _provider_returning(VALID_KEY_POINTS)

    outline = generate_outline(LECTURE, CLOS, provider=provider)

    assert outline.totalDurationMin == sum(kp.durationMin for kp in outline.keyPoints)


def test_generate_outline_defaults_duration_when_lecture_has_none():
    lecture = Lecture(id="9", week="1", topic="x", name="x", durationMin=None)
    provider = _provider_returning(VALID_KEY_POINTS)

    generate_outline(lecture, CLOS, provider=provider)

    _, user_prompt = provider.complete_json.call_args[0]
    assert "Scheduled duration: 60 minutes" in user_prompt


def test_generate_outline_uses_default_provider_when_none_given(monkeypatch):
    import app.outline_service as svc

    fake_provider = _provider_returning(VALID_KEY_POINTS)
    monkeypatch.setattr(svc, "get_provider", lambda: fake_provider)

    outline = generate_outline(LECTURE, CLOS)

    assert outline.lectureId == "3"
    fake_provider.complete_json.assert_called_once()
