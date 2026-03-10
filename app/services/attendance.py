from __future__ import annotations

import os
import uuid
from datetime import date as dt_date
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.exceptions import AppException
from app.core.face import extract_single_face_embedding
from app.models import Attendance
from app.repositories.attendances import AttendanceRepository
from app.repositories.class_subject_schedules import \
    ClassSubjectScheduleRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.student_faces import StudentFaceRepository
from app.repositories.students import StudentRepository


def _now_local() -> datetime:
    tz_name = os.getenv("ATTENDANCE_TZ", "Asia/Jakarta")
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz)


def _python_weekday_to_api_day_of_week(d: datetime) -> int:
    return (d.weekday() + 1) % 7


def _ensure_within_schedule_window(*, schedule, now: datetime) -> None:
    day_of_week = getattr(schedule, "day_of_week", None)
    start_time = getattr(schedule, "start_time", None)
    end_time = getattr(schedule, "end_time", None)

    if day_of_week is None or start_time is None or end_time is None:
        raise AppException(
            status_code=500,
            message="schedule time is not configured",
            meta={
                "schedule_id": str(getattr(schedule, "id", "")),
                "day_of_week": day_of_week,
                "start_time": (
                    start_time.isoformat()
                    if getattr(start_time, "isoformat", None)
                    else None
                ),
                "end_time": (
                    end_time.isoformat()
                    if getattr(end_time, "isoformat", None)
                    else None
                ),
            },
        )

    early_minutes = int(os.getenv("ATTENDANCE_EARLY_MINUTES", "0"))
    late_minutes = int(os.getenv("ATTENDANCE_LATE_MINUTES", "0"))

    now_day = _python_weekday_to_api_day_of_week(now)
    expected_day = int(day_of_week)

    today = now.date()
    tz = now.tzinfo

    is_overnight = end_time <= start_time
    if not is_overnight:
        if now_day != expected_day:
            raise AppException(
                status_code=422,
                message="attendance is not allowed outside schedule time",
                meta={
                    "reason": "day_mismatch",
                    "now_day_of_week": now_day,
                    "schedule_day_of_week": expected_day,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "timezone": str(tz),
                },
            )
        window_start = datetime.combine(today, start_time).replace(tzinfo=tz)
        window_end = datetime.combine(today, end_time).replace(tzinfo=tz)
    else:
        next_day = (expected_day + 1) % 7
        if now_day == expected_day:
            window_start = datetime.combine(today, start_time).replace(
                tzinfo=tz
            )
            window_end = datetime.combine(
                today + timedelta(days=1),
                end_time,
            ).replace(tzinfo=tz)
        elif now_day == next_day:
            window_start = datetime.combine(
                today - timedelta(days=1),
                start_time,
            ).replace(tzinfo=tz)
            window_end = datetime.combine(today, end_time).replace(tzinfo=tz)
        else:
            raise AppException(
                status_code=422,
                message="attendance is not allowed outside schedule time",
                meta={
                    "reason": "day_mismatch",
                    "now_day_of_week": now_day,
                    "schedule_day_of_week": expected_day,
                    "schedule_next_day_of_week": next_day,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "timezone": str(tz),
                },
            )

    window_start = window_start - timedelta(minutes=early_minutes)
    window_end = window_end + timedelta(minutes=late_minutes)

    if now < window_start or now > window_end:
        raise AppException(
            status_code=422,
            message="attendance is not allowed outside schedule time",
            meta={
                "reason": "time_outside_window",
                "now": now.isoformat(),
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "schedule_day_of_week": expected_day,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "early_minutes": early_minutes,
                "late_minutes": late_minutes,
                "timezone": str(tz),
            },
        )


def verify_attendance_by_face(
    *,
    schedule_repo: ClassSubjectScheduleRepository,
    enrollment_repo: EnrollmentRepository,
    face_repo: StudentFaceRepository,
    attendance_repo: AttendanceRepository,
    student_repo: StudentRepository,
    schedule_id: uuid.UUID,
    image_bytes: bytes,
) -> dict:
    schedule = schedule_repo.get(schedule_id)
    if not schedule:
        raise AppException(
            status_code=404,
            message="schedule not found",
            meta={"schedule_id": str(schedule_id)},
        )

    now = _now_local()
    enforce_schedule_value = os.getenv("ATTENDANCE_ENFORCE_SCHEDULE", "0")
    enforce_schedule = enforce_schedule_value.lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if enforce_schedule:
        _ensure_within_schedule_window(schedule=schedule, now=now)

    student_ids = enrollment_repo.list_student_ids_by_class_instance(
        class_instance_id=schedule.class_instance_id
    )
    if not student_ids:
        return {
            "matched": False,
            "reason": "no enrolled students",
            "confidence": None,
            "student_id": None,
            "student_name": None,
            "attendance_id": None,
            "already_recorded": False,
        }

    query_embedding = extract_single_face_embedding(image_bytes)
    matches = face_repo.best_matches_for_students(
        embedding=query_embedding,
        student_ids=student_ids,
        limit=2,
    )
    if not matches:
        return {
            "matched": False,
            "reason": "no enrolled faces",
            "confidence": None,
            "student_id": None,
            "student_name": None,
            "attendance_id": None,
            "already_recorded": False,
        }

    best_student_id, best_distance = matches[0]
    best_similarity = 1.0 - float(best_distance)

    second_similarity: float | None = None
    if len(matches) > 1:
        second_similarity = 1.0 - float(matches[1][1])

    match_threshold = float(os.getenv("FACE_MATCH_THRESHOLD", "0.4"))
    margin_threshold = float(os.getenv("FACE_MATCH_MARGIN", "0.05"))

    if best_similarity < match_threshold:
        return {
            "matched": False,
            "reason": "below threshold",
            "confidence": best_similarity,
            "student_id": None,
            "student_name": None,
            "attendance_id": None,
            "already_recorded": False,
        }

    if (
        second_similarity is not None
        and best_similarity - second_similarity < margin_threshold
    ):
        return {
            "matched": False,
            "reason": "ambiguous match",
            "confidence": best_similarity,
            "student_id": None,
            "student_name": None,
            "attendance_id": None,
            "already_recorded": False,
        }

    student = student_repo.get(best_student_id)
    student_name = getattr(student, "name", None)

    today = now.date()
    current_time = now.time().replace(microsecond=0, tzinfo=None)

    existing = attendance_repo.get_by_student_schedule_date(
        student_id=best_student_id,
        schedule_id=schedule_id,
        date=today,
    )
    if existing:
        return {
            "matched": True,
            "reason": "already recorded",
            "confidence": float(existing.confidence),
            "student_id": str(existing.student_id),
            "student_name": student_name,
            "attendance_id": str(existing.id),
            "already_recorded": True,
        }

    attendance = Attendance(
        student_id=best_student_id,
        schedule_id=schedule_id,
        date=today,
        time=current_time,
        status="PRESENT",
        confidence=best_similarity,
    )
    attendance_repo.add(attendance)
    attendance_repo.db.commit()
    attendance_repo.db.refresh(attendance)

    return {
        "matched": True,
        "reason": "recorded",
        "confidence": best_similarity,
        "student_id": str(attendance.student_id),
        "student_name": student_name,
        "attendance_id": str(attendance.id),
        "already_recorded": False,
    }


def list_attendance_records(
    attendance_repo: AttendanceRepository,
    *,
    offset: int,
    limit: int,
    class_instance_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
    teacher_id: uuid.UUID | None = None,
    date: dt_date | None = None,
    student_name: str | None = None,
) -> tuple[list[dict], int]:
    attendances, total = attendance_repo.list_paginated(
        offset=offset,
        limit=limit,
        class_instance_id=class_instance_id,
        subject_id=subject_id,
        teacher_id=teacher_id,
        date=date,
        student_name=student_name,
    )

    items: list[dict] = []
    for a in attendances:
        student = getattr(a, "student", None)
        schedule = getattr(a, "schedule", None)
        subject = getattr(schedule, "subject", None) if schedule else None
        teacher = getattr(schedule, "teacher", None) if schedule else None
        class_instance = (
            getattr(schedule, "class_instance", None) if schedule else None
        )
        class_template = (
            getattr(class_instance, "class_template", None)
            if class_instance
            else None
        )

        grade = getattr(class_template, "grade", None)
        class_name = getattr(class_template, "name", None)
        if grade is not None and class_name:
            class_label = f"Kelas {grade}.{class_name}"
        else:
            class_label = "-"

        date_value = getattr(a, "date", None)
        time_value = getattr(a, "time", None)

        items.append(
            {
                "id": str(getattr(a, "id", "")),
                "date": (
                    date_value.isoformat()
                    if getattr(date_value, "isoformat", None)
                    else None
                ),
                "time": (
                    time_value.isoformat()
                    if getattr(time_value, "isoformat", None)
                    else None
                ),
                "status": getattr(a, "status", None),
                "confidence": float(getattr(a, "confidence", 0.0)),
                "student_id": str(getattr(a, "student_id", "")),
                "student_nis": getattr(student, "nis", None),
                "student_name": getattr(student, "name", None),
                "schedule_id": str(getattr(a, "schedule_id", "")),
                "class_instance_id": (
                    str(getattr(schedule, "class_instance_id", ""))
                    if schedule
                    else None
                ),
                "class_label": class_label,
                "subject_id": (
                    str(getattr(schedule, "subject_id", ""))
                    if schedule
                    else None
                ),
                "subject_name": getattr(subject, "name", None),
                "teacher_id": (
                    str(getattr(schedule, "teacher_id", ""))
                    if schedule
                    else None
                ),
                "teacher_name": getattr(teacher, "name", None),
            }
        )

    return items, total
