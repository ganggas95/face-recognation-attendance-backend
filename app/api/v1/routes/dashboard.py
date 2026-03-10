import os
import uuid
from datetime import date as dt_date
from datetime import datetime
from datetime import time as dt_time
from zoneinfo import ZoneInfo

from app.core.deps import (get_academic_year_repository,
                           get_attendance_repository,
                           get_class_subject_schedule_repository,
                           get_current_user, get_enrollment_repository,
                           get_gate_attendance_repository,
                           get_school_setting_repository,
                           get_student_repository, get_teacher_repository)
from app.models import (AcademicYear, Attendance, Class, ClassInstance,
                        GateAttendance, Student, StudentClassEnrollment, User)
from app.repositories.academic_years import AcademicYearRepository
from app.repositories.attendances import AttendanceRepository
from app.repositories.class_subject_schedules import \
    ClassSubjectScheduleRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.gate_attendances import GateAttendanceRepository
from app.repositories.school_settings import SchoolSettingRepository
from app.repositories.students import StudentRepository
from app.repositories.teachers import TeacherRepository
from app.schemas.api_response import ApiResponse, build_response
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select

router = APIRouter()


def _now_local() -> datetime:
    tz_name = os.getenv("ATTENDANCE_TZ", "Asia/Jakarta")
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz)


def _parse_late_after() -> dt_time:
    raw = os.getenv("GATE_LATE_AFTER", "07:00:00")
    try:
        value = dt_time.fromisoformat(raw)
        return value.replace(microsecond=0, tzinfo=None)
    except Exception:
        return dt_time(hour=7, minute=0, second=0)


def _default_gate_out_time() -> dt_time:
    return dt_time(hour=15, minute=0, second=0)


def _get_gate_in_time(
    repo: SchoolSettingRepository,
) -> dt_time:
    settings = repo.get_default()
    if settings is None:
        settings = repo.upsert_default(
            gate_in_time=_parse_late_after(),
            gate_out_time=_default_gate_out_time(),
        )
        repo.db.commit()
        repo.db.refresh(settings)
    value = getattr(settings, "gate_in_time", None)
    if getattr(value, "isoformat", None):
        return value.replace(microsecond=0, tzinfo=None)
    return _parse_late_after()


def _label_gender(value: str | None) -> str:
    if not value:
        return "Tidak diisi"
    v = value.strip().upper()
    if v in {"L", "LAKI-LAKI", "LAKI", "MALE"}:
        return "Laki-laki"
    if v in {"P", "PEREMPUAN", "FEMALE"}:
        return "Perempuan"
    return value.strip()


def _label_class(*, grade: int | None, name: str | None) -> str:
    if grade is None or not name:
        return "-"
    return f"Kelas {grade}.{name}"


def _iso_time(value) -> str | None:
    if getattr(value, "isoformat", None):
        return value.isoformat()
    return None


@router.get("/summary", response_model=ApiResponse)
def summary(
    student_repo: StudentRepository = Depends(get_student_repository),
    enrollment_repo: EnrollmentRepository = Depends(get_enrollment_repository),
    attendance_repo: AttendanceRepository = Depends(get_attendance_repository),
    gate_repo: GateAttendanceRepository = Depends(
        get_gate_attendance_repository
    ),
    school_setting_repo: SchoolSettingRepository = Depends(
        get_school_setting_repository
    ),
    schedule_repo: ClassSubjectScheduleRepository = Depends(
        get_class_subject_schedule_repository
    ),
    academic_year_repo: AcademicYearRepository = Depends(
        get_academic_year_repository
    ),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
    current_user: User = Depends(get_current_user),
    date: dt_date | None = Query(default=None),
) -> ApiResponse:
    role = str(getattr(current_user, "role", "")).strip().upper()
    now = _now_local()
    target_date = date or now.date()

    gender_rows = list(
        student_repo.db.execute(
            select(Student.gender, func.count(Student.id))
            .select_from(Student)
            .group_by(Student.gender)
        ).all()
    )
    gender_items: list[dict] = []
    for gender, count in gender_rows:
        gender_items.append(
            {
                "key": (gender or "").strip() or "UNKNOWN",
                "label": _label_gender(gender),
                "count": int(count or 0),
            }
        )
    gender_items = sorted(gender_items, key=lambda x: x["count"], reverse=True)

    active_year = academic_year_repo.get_active()
    class_stmt = (
        select(
            ClassInstance.id,
            Class.grade,
            Class.name,
            func.count(StudentClassEnrollment.id),
        )
        .select_from(StudentClassEnrollment)
        .join(StudentClassEnrollment.class_instance)
        .join(ClassInstance.class_template)
    )
    if active_year:
        class_stmt = (
            class_stmt.join(ClassInstance.academic_year)
            .where(AcademicYear.is_active.is_(True))
        )
    class_stmt = class_stmt.group_by(ClassInstance.id, Class.grade, Class.name)
    class_rows = list(student_repo.db.execute(class_stmt).all())
    class_items: list[dict] = []
    for class_instance_id, grade, name, count in class_rows:
        class_items.append(
            {
                "class_instance_id": str(class_instance_id),
                "label": _label_class(grade=grade, name=name),
                "count": int(count or 0),
            }
        )
    class_items = sorted(class_items, key=lambda x: x["count"], reverse=True)

    late_after = _get_gate_in_time(school_setting_repo)

    total_students = 0
    if active_year:
        total_students = int(
            student_repo.db.scalar(
                select(
                    func.count(
                        func.distinct(StudentClassEnrollment.student_id)
                    )
                )
                .select_from(StudentClassEnrollment)
                .join(StudentClassEnrollment.class_instance)
                .join(ClassInstance.academic_year)
                .where(AcademicYear.is_active.is_(True))
            )
            or 0
        )
    else:
        total_students = int(
            student_repo.db.scalar(
                select(func.count(Student.id)).select_from(Student)
            )
            or 0
        )

    in_count = int(
        gate_repo.db.scalar(
            select(func.count(func.distinct(GateAttendance.student_id)))
            .select_from(GateAttendance)
            .where(GateAttendance.date == target_date)
            .where(GateAttendance.direction == "IN")
        )
        or 0
    )
    out_count = int(
        gate_repo.db.scalar(
            select(func.count(func.distinct(GateAttendance.student_id)))
            .select_from(GateAttendance)
            .where(GateAttendance.date == target_date)
            .where(GateAttendance.direction == "OUT")
        )
        or 0
    )
    late_count = int(
        gate_repo.db.scalar(
            select(func.count(GateAttendance.id))
            .select_from(GateAttendance)
            .where(GateAttendance.date == target_date)
            .where(GateAttendance.direction == "IN")
            .where(GateAttendance.time > late_after)
        )
        or 0
    )

    gate_summary = {
        "date": target_date.isoformat(),
        "total_students": total_students,
        "late_after": late_after.isoformat(),
        "late_count": late_count,
        "in_recorded": in_count,
        "in_missing": max(total_students - in_count, 0),
        "out_recorded": out_count,
        "out_missing": max(total_students - out_count, 0),
    }

    teacher_attendance: dict | None = None
    if role == "TEACHER":
        teacher = teacher_repo.get_by_user_id(current_user.id)
        if teacher:
            weekday = now.weekday()
            day_of_week = (weekday + 1) % 7
            schedules = schedule_repo.list_options(
                active_academic_year_only=True,
                teacher_id=teacher.id,
            )
            today_schedules = [
                s
                for s in schedules
                if getattr(s, "day_of_week", None) == day_of_week
            ]
            schedule_ids = [
                getattr(s, "id")
                for s in today_schedules
                if getattr(s, "id", None)
            ]
            class_instance_ids = sorted(
                {
                    getattr(s, "class_instance_id")
                    for s in today_schedules
                    if getattr(s, "class_instance_id", None)
                }
            )

            class_totals: dict[uuid.UUID, int] = {}
            if class_instance_ids:
                totals_rows = list(
                    enrollment_repo.db.execute(
                        select(
                            StudentClassEnrollment.class_instance_id,
                            func.count(StudentClassEnrollment.id),
                        )
                        .select_from(StudentClassEnrollment)
                        .join(StudentClassEnrollment.class_instance)
                        .join(ClassInstance.academic_year)
                        .where(AcademicYear.is_active.is_(True))
                        .where(
                            StudentClassEnrollment.class_instance_id.in_(
                                class_instance_ids
                            )
                        )
                        .group_by(StudentClassEnrollment.class_instance_id)
                    ).all()
                )
                class_totals = {
                    class_instance_id: int(count or 0)
                    for class_instance_id, count in totals_rows
                }

            present_by_schedule: dict[uuid.UUID, int] = {}
            if schedule_ids:
                present_rows = list(
                    attendance_repo.db.execute(
                        select(
                            Attendance.schedule_id,
                            func.count(Attendance.id),
                        )
                        .select_from(Attendance)
                        .where(Attendance.date == target_date)
                        .where(Attendance.schedule_id.in_(schedule_ids))
                        .group_by(Attendance.schedule_id)
                    ).all()
                )
                present_by_schedule = {
                    schedule_id: int(count or 0)
                    for schedule_id, count in present_rows
                }

            items: list[dict] = []
            for s in today_schedules:
                class_instance = getattr(s, "class_instance", None)
                class_template = (
                    getattr(class_instance, "class_template", None)
                    if class_instance
                    else None
                )
                subject = getattr(s, "subject", None)
                schedule_id = getattr(s, "id", None)
                class_instance_id = getattr(s, "class_instance_id", None)
                total_in_class = (
                    class_totals.get(class_instance_id, 0)
                    if class_instance_id
                    else 0
                )
                present = (
                    present_by_schedule.get(schedule_id, 0)
                    if schedule_id
                    else 0
                )
                items.append(
                    {
                        "schedule_id": (
                            str(schedule_id) if schedule_id else None
                        ),
                        "class_instance_id": (
                            str(class_instance_id)
                            if class_instance_id
                            else None
                        ),
                        "class_label": _label_class(
                            grade=getattr(class_template, "grade", None),
                            name=getattr(class_template, "name", None),
                        ),
                        "subject_id": str(getattr(s, "subject_id", "")),
                        "subject_name": getattr(subject, "name", None),
                        "start_time": _iso_time(
                            getattr(s, "start_time", None)
                        ),
                        "end_time": _iso_time(getattr(s, "end_time", None)),
                        "room": getattr(s, "room", None),
                        "total_students": total_in_class,
                        "present": present,
                        "absent": max(total_in_class - present, 0),
                    }
                )

            teacher_attendance = {
                "date": target_date.isoformat(),
                "day_of_week": day_of_week,
                "items": items,
            }

    return build_response(
        status=status.HTTP_200_OK,
        data={
            "user": {"id": str(getattr(current_user, "id", "")), "role": role},
            "students": {
                "by_gender": gender_items,
                "by_class": class_items,
            },
            "teacher_attendance": teacher_attendance,
            "gate": gate_summary,
        },
        message="ok",
        meta={},
    )
