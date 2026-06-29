from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class InstructorProfile(BaseModel):
    name: str
    title: str
    department: str
    faculty: str
    university: str = "มหาวิทยาลัยขอนแก่น"
    courseCode: str
    courseName: str
    academicYear: str
    semester: str
    section: str = ""


class PLO(BaseModel):
    id: str
    text: str


class CLO(BaseModel):
    id: str
    text: str
    ploRefs: List[str] = []


class Lecture(BaseModel):
    id: str
    week: str
    topic: str
    name: str
    durationMin: Optional[int] = None
    cloRefs: List[str] = []


class ExtractedCourse(BaseModel):
    courseCode: str
    courseName: str
    PLOs: List[PLO] = []
    CLOs: List[CLO] = []
    lectures: List[Lecture] = []


class OutlineGrounding(BaseModel):
    slidesText: Optional[str] = None
    brief: Optional[str] = None


class KeyPoint(BaseModel):
    seq: int
    title: str
    objective: str
    content: str
    durationMin: int
    teachingMethod: str  # lecture | interactive | quiz
    cloRefs: List[str] = []
    materials: str = ""
    assessment: str = ""


class LectureOutline(BaseModel):
    lectureId: str
    totalDurationMin: int
    keyPoints: List[KeyPoint]
