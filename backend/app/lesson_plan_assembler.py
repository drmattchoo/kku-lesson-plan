from __future__ import annotations

from app.schemas import ExtractedCourse, InstructorProfile, Lecture, LectureOutline


def _format_hours(total_minutes: int) -> str:
    hours = total_minutes / 60
    if hours == int(hours):
        return str(int(hours))
    return f"{hours:.1f}"


def build_render_context(
    instructor: InstructorProfile,
    course: ExtractedCourse,
    lecture: Lecture,
    outline: LectureOutline,
    session_date: str = "",
    session_time: str = "",
) -> dict:
    """Map session data into the context shape app.template_binder expects (the
    same shape proven in M1's render-proof gate). The official KKU template only
    shows the date/time block on the FIRST table row, blank for the rest — confirmed
    against the real filled examples (PT_ANS_2569.docx, PS_ANS_2569.docx) — so
    timeLabel is only set on keyPoints[0], not computed per row."""
    key_points = [
        {
            "timeLabel": f"{session_date}\n{session_time}".strip() if i == 0 else "",
            "title": kp.title,
            "objective": kp.objective,
            "content": kp.content,
            "durationMin": kp.durationMin,
            "teachingMethod": kp.teachingMethod,
            "cloRefs": kp.cloRefs,
            "materials": kp.materials,
            "assessment": kp.assessment,
        }
        for i, kp in enumerate(outline.keyPoints)
    ]

    return {
        "semester": course.semester,
        "academicYear": course.academicYear,
        "courseCode": course.courseCode,
        "courseName": course.courseName,
        "lectureTopic": lecture.topic,
        "totalDurationHours": _format_hours(outline.totalDurationMin),
        "learners": course.learners,
        "instructorName": instructor.name,
        "department": course.department,
        "sessionDate": session_date,
        "sessionTime": session_time,
        "PLOs": [plo.model_dump() for plo in course.PLOs],
        "CLOs": [clo.model_dump() for clo in course.CLOs],
        "keyPoints": key_points,
        "totalDurationMin": outline.totalDurationMin,
        "references": [],
    }
