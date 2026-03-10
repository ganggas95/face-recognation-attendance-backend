from app.models.academic_years import AcademicYear
from app.models.attendances import Attendance
from app.models.class_instances import ClassInstance
from app.models.class_subject_assignments import ClassSubjectAssignment
from app.models.class_subject_schedules import ClassSubjectSchedule
from app.models.classes import Class
from app.models.enrollments import StudentClassEnrollment
from app.models.gate_attendances import GateAttendance
from app.models.school_settings import SchoolSetting
from app.models.student_attendances import StudentAttendance
from app.models.student_faces import StudentFace
from app.models.students import Student
from app.models.subjects import Subject
from app.models.teachers import Teacher
from app.models.users import User

__all__ = [
    "AcademicYear",
    "Attendance",
    "ClassSubjectAssignment",
    "ClassSubjectSchedule",
    "Class",
    "ClassInstance",
    "Student",
    "StudentClassEnrollment",
    "GateAttendance",
    "SchoolSetting",
    "StudentAttendance",
    "StudentFace",
    "Subject",
    "Teacher",
    "User",
]
