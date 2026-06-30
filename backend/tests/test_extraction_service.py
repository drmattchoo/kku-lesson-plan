from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.extraction_service import extract_course
from app.schemas import ExtractedCourse


def _provider_returning(payload: dict):
    provider = MagicMock()
    provider.complete_json.return_value = payload
    return provider


def test_extract_course_parses_valid_payload():
    provider = _provider_returning(
        {
            "courseCode": "MD672305",
            "courseName": "Physiology for Dental Students",
            "PLOs": [],
            "CLOs": [
                {"id": "1", "text": "อธิบายกลไกการทำงานของระบบต่าง ๆ ของร่างกาย", "ploRefs": []},
            ],
            "lectures": [
                {
                    "id": "1",
                    "week": "1",
                    "topic": "แนะนำรายวิชา",
                    "name": "Course orientation",
                    "durationMin": 5,
                    "cloRefs": [],
                },
            ],
        }
    )

    result = extract_course("some มคอ text", provider=provider)

    assert isinstance(result, ExtractedCourse)
    assert result.courseCode == "MD672305"
    assert result.PLOs == []
    assert result.CLOs[0].id == "1"
    assert result.lectures[0].durationMin == 5
    provider.complete_json.assert_called_once()


def test_extract_course_parses_term_and_audience_fields():
    provider = _provider_returning(
        {
            "courseCode": "MD672305",
            "courseName": "Physiology for Dental Students",
            "academicYear": "2569",
            "semester": "1",
            "department": "สาขาวิชาสรีรวิทยา",
            "faculty": "คณะแพทยศาสตร์",
            "university": "มหาวิทยาลัยขอนแก่น",
            "learners": "นักศึกษาทันตแพทย์ ชั้นปีที่ 2",
            "PLOs": [],
            "CLOs": [],
            "lectures": [],
        }
    )

    result = extract_course("text", provider=provider)

    assert result.academicYear == "2569"
    assert result.semester == "1"
    assert result.department == "สาขาวิชาสรีรวิทยา"
    assert result.learners == "นักศึกษาทันตแพทย์ ชั้นปีที่ 2"


def test_extract_course_defaults_term_and_audience_fields_to_empty_when_absent():
    # course specs vary in format — these fields aren't always stated
    provider = _provider_returning(
        {"courseCode": "MD1", "courseName": "X", "PLOs": [], "CLOs": [], "lectures": []}
    )

    result = extract_course("text", provider=provider)

    assert result.academicYear == ""
    assert result.semester == ""
    assert result.department == ""
    assert result.learners == ""


def test_extract_course_allows_empty_plos_for_real_world_doc():
    # the real DT.docx มคอ-3 has a PLO/CLO mapping table that's just headers with no
    # data rows — extraction must not invent PLOs to fill that gap.
    provider = _provider_returning(
        {
            "courseCode": "MD672305",
            "courseName": "Physiology for Dental Students",
            "PLOs": [],
            "CLOs": [{"id": "1", "text": "x", "ploRefs": []}],
            "lectures": [],
        }
    )

    result = extract_course("text", provider=provider)

    assert result.PLOs == []


def test_extract_course_raises_on_missing_required_field():
    provider = _provider_returning({"courseName": "Missing course code"})

    with pytest.raises(ValidationError):
        extract_course("text", provider=provider)


def test_extract_course_retries_once_then_succeeds_on_bad_first_response():
    provider = MagicMock()
    provider.complete_json.side_effect = [
        {"courseName": "missing courseCode on first attempt"},
        {"courseCode": "MD1", "courseName": "Recovered", "PLOs": [], "CLOs": [], "lectures": []},
    ]

    result = extract_course("text", provider=provider)

    assert result.courseCode == "MD1"
    assert provider.complete_json.call_count == 2


def test_extract_course_uses_default_provider_when_none_given(monkeypatch):
    import app.extraction_service as svc

    fake_provider = _provider_returning(
        {"courseCode": "X", "courseName": "Y", "PLOs": [], "CLOs": [], "lectures": []}
    )
    monkeypatch.setattr(svc, "get_provider", lambda: fake_provider)

    result = extract_course("text")

    assert result.courseCode == "X"
    fake_provider.complete_json.assert_called_once()
