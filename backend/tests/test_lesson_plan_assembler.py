from app.lesson_plan_assembler import build_render_context
from app.schemas import CLO, ExtractedCourse, InstructorProfile, KeyPoint, Lecture, LectureOutline, PLO

INSTRUCTOR = InstructorProfile(
    name="ผศ.ดร. สมชาย ใจดี",
    title="ผู้ช่วยศาสตราจารย์",
    department="สาขาวิชาสรีรวิทยา",
    faculty="คณะแพทยศาสตร์",
    courseCode="MD672305",
    courseName="Physiology for Dental Students",
    academicYear="2569",
    semester="1",
    learners="นักศึกษาทันตแพทย์ ชั้นปีที่ 2",
)

COURSE = ExtractedCourse(
    courseCode="MD672305",
    courseName="Physiology for Dental Students",
    PLOs=[PLO(id="4", text="x")],
    CLOs=[CLO(id="1", text="y", ploRefs=["4"])],
    lectures=[Lecture(id="4", week="1", topic="สรีรวิทยาระบบประสาท", name="x", durationMin=120, cloRefs=["1"])],
)

LECTURE = COURSE.lectures[0]

OUTLINE = LectureOutline(
    lectureId="4",
    totalDurationMin=90,
    keyPoints=[
        KeyPoint(seq=1, title="A", objective="objA", content="c1", durationMin=30,
                 teachingMethod="lecture", cloRefs=["1"], materials="m", assessment="a"),
        KeyPoint(seq=2, title="B", objective="objB", content="c2", durationMin=60,
                 teachingMethod="quiz", cloRefs=[], materials="m2", assessment="a2"),
    ],
)


def test_build_render_context_maps_core_fields():
    ctx = build_render_context(INSTRUCTOR, COURSE, LECTURE, OUTLINE, session_date="1 ก.ค. 2569", session_time="09:00-10:30")

    assert ctx["courseCode"] == "MD672305"
    assert ctx["lectureTopic"] == "สรีรวิทยาระบบประสาท"
    assert ctx["learners"] == "นักศึกษาทันตแพทย์ ชั้นปีที่ 2"
    assert ctx["instructorName"] == "ผศ.ดร. สมชาย ใจดี"
    assert ctx["totalDurationMin"] == 90
    assert ctx["PLOs"][0]["id"] == "4"
    assert ctx["CLOs"][0]["ploRefs"] == ["4"]


def test_build_render_context_formats_whole_and_fractional_hours():
    ctx_whole = build_render_context(INSTRUCTOR, COURSE, LECTURE, OUTLINE)
    assert ctx_whole["totalDurationHours"] == "1.5"  # 90 min

    outline_60 = OUTLINE.model_copy(update={"totalDurationMin": 60})
    ctx_60 = build_render_context(INSTRUCTOR, COURSE, LECTURE, outline_60)
    assert ctx_60["totalDurationHours"] == "1"


def test_build_render_context_sets_time_label_only_on_first_keypoint():
    ctx = build_render_context(INSTRUCTOR, COURSE, LECTURE, OUTLINE, session_date="1 ก.ค. 2569", session_time="09:00-10:30")

    assert ctx["keyPoints"][0]["timeLabel"] == "1 ก.ค. 2569\n09:00-10:30"
    assert ctx["keyPoints"][1]["timeLabel"] == ""


def test_build_render_context_keypoint_carries_cloRefs_for_render_binder_to_compute():
    ctx = build_render_context(INSTRUCTOR, COURSE, LECTURE, OUTLINE)
    assert ctx["keyPoints"][0]["cloRefs"] == ["1"]
    assert ctx["keyPoints"][1]["cloRefs"] == []
