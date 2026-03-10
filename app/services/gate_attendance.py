from __future__ import annotations

import os
import uuid
from datetime import date as dt_date
from datetime import datetime
from datetime import time as dt_time
from zoneinfo import ZoneInfo

from app.core.exceptions import AppException
from app.core.face import extract_single_face_embedding
from app.models import GateAttendance
from app.repositories.academic_years import AcademicYearRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.gate_attendances import GateAttendanceRepository
from app.repositories.student_attendances import StudentAttendanceRepository
from app.repositories.student_faces import StudentFaceRepository
from app.repositories.students import StudentRepository


def _now_local() -> datetime:
    tz_name = os.getenv("ATTENDANCE_TZ", "Asia/Jakarta")
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz)


def _normalize_direction(direction: str) -> str:
    d = direction.strip().upper()
    if d not in {"IN", "OUT"}:
        raise AppException(
            status_code=422,
            message="invalid direction",
            meta={"direction": direction},
        )
    return d


def verify_gate_attendance_by_face(
    *,
    academic_year_repo: AcademicYearRepository,
    enrollment_repo: EnrollmentRepository,
    face_repo: StudentFaceRepository,
    gate_attendance_repo: GateAttendanceRepository,
    student_attendance_repo: StudentAttendanceRepository,
    student_repo: StudentRepository,
    recorded_by_user_id: uuid.UUID,
    direction: str,
    gate_in_time: dt_time,
    image_bytes: bytes,
) -> dict:
    normalized_direction = _normalize_direction(direction)

    active_year = academic_year_repo.get_active()
    if active_year:
        enrollments = enrollment_repo.list_by_student_ids(
            student_ids=None,
            active_academic_year_only=True,
        )
        student_ids = sorted({e.student_id for e in enrollments})
        if not student_ids:
            return {
                "matched": False,
                "reason": "no enrolled students",
                "confidence": None,
                "student_id": None,
                "student_name": None,
                "gate_attendance_id": None,
                "already_recorded": False,
                "direction": normalized_direction,
            }
    else:
        students = student_repo.list()
        student_ids = [s.id for s in students]
        if not student_ids:
            return {
                "matched": False,
                "reason": "no students",
                "confidence": None,
                "student_id": None,
                "student_name": None,
                "gate_attendance_id": None,
                "already_recorded": False,
                "direction": normalized_direction,
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
            "gate_attendance_id": None,
            "already_recorded": False,
            "direction": normalized_direction,
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
            "gate_attendance_id": None,
            "already_recorded": False,
            "direction": normalized_direction,
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
            "gate_attendance_id": None,
            "already_recorded": False,
            "direction": normalized_direction,
        }

    student = student_repo.get(best_student_id)
    student_name = getattr(student, "name", None)

    now = _now_local()
    today: dt_date = now.date()
    current_time: dt_time = now.time().replace(microsecond=0, tzinfo=None)

    existing = gate_attendance_repo.get_by_student_date_direction(
        student_id=best_student_id,
        date=today,
        direction=normalized_direction,
    )
    if existing:
        existing_time = existing.time
        computed_status = (
            "TELAT"
            if existing_time is not None and existing_time > gate_in_time
            else "TEPAT_WAKTU"
        )
        student_attendance_repo.upsert_from_gate(
            student_id=best_student_id,
            date=today,
            direction=normalized_direction,
            gate_attendance_id=existing.id,
            computed_status=computed_status,
        )
        student_attendance_repo.db.commit()
        return {
            "matched": True,
            "reason": "already recorded",
            "confidence": float(existing.confidence),
            "student_id": str(existing.student_id),
            "student_name": student_name,
            "gate_attendance_id": str(existing.id),
            "already_recorded": True,
            "direction": normalized_direction,
            "date": today.isoformat(),
            "time": existing_time.isoformat(),
            "is_late": bool(
                normalized_direction == "IN"
                and existing_time is not None
                and existing_time > gate_in_time
            ),
        }

    item = GateAttendance(
        student_id=best_student_id,
        recorded_by_user_id=recorded_by_user_id,
        date=today,
        time=current_time,
        direction=normalized_direction,
        confidence=best_similarity,
    )
    gate_attendance_repo.add(item)
    gate_attendance_repo.db.flush()
    computed_status = (
        "TELAT"
        if normalized_direction == "IN" and current_time > gate_in_time
        else "TEPAT_WAKTU"
    )
    student_attendance_repo.upsert_from_gate(
        student_id=best_student_id,
        date=today,
        direction=normalized_direction,
        gate_attendance_id=item.id,
        computed_status=computed_status,
    )
    gate_attendance_repo.db.commit()
    gate_attendance_repo.db.refresh(item)

    return {
        "matched": True,
        "reason": "recorded",
        "confidence": best_similarity,
        "student_id": str(item.student_id),
        "student_name": student_name,
        "gate_attendance_id": str(item.id),
        "already_recorded": False,
        "direction": normalized_direction,
        "date": today.isoformat(),
        "time": current_time.isoformat(),
        "is_late": bool(
            normalized_direction == "IN"
            and current_time is not None
            and current_time > gate_in_time
        ),
    }


def list_gate_attendance_records(
    gate_attendance_repo: GateAttendanceRepository,
    *,
    gate_in_time: dt_time,
    offset: int,
    limit: int,
    date: dt_date | None = None,
    direction: str | None = None,
    student_name: str | None = None,
    recorded_by_user_id: uuid.UUID | None = None,
) -> tuple[list[dict], int]:
    items, total = gate_attendance_repo.list_paginated(
        offset=offset,
        limit=limit,
        date=date,
        direction=direction,
        student_name=student_name,
        recorded_by_user_id=recorded_by_user_id,
    )

    payload_items: list[dict] = []
    for a in items:
        student = getattr(a, "student", None)
        recorder = getattr(a, "recorded_by_user", None)
        date_value = getattr(a, "date", None)
        time_value = getattr(a, "time", None)
        direction_value = getattr(a, "direction", None)
        payload_items.append(
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
                "direction": direction_value,
                "confidence": float(getattr(a, "confidence", 0.0)),
                "student_id": str(getattr(a, "student_id", "")),
                "student_nis": getattr(student, "nis", None),
                "student_name": getattr(student, "name", None),
                "recorded_by_user_id": str(
                    getattr(a, "recorded_by_user_id", "")
                ),
                "recorded_by_email": getattr(recorder, "email", None),
                "is_late": bool(
                    direction_value == "IN"
                    and time_value is not None
                    and time_value > gate_in_time
                ),
            }
        )

    return payload_items, total
