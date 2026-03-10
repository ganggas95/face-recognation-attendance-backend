from __future__ import annotations

import uuid
from datetime import date as dt_date
from datetime import time as dt_time

from app.models.gate_attendances import GateAttendance
from app.models.student_attendances import StudentAttendance
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session


class StudentAttendanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_student_date(
        self,
        student_id: uuid.UUID,
        date: dt_date,
    ) -> StudentAttendance | None:
        stmt = (
            select(StudentAttendance)
            .where(
                StudentAttendance.student_id == student_id,
                StudentAttendance.date == date,
            )
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def get_or_create(
        self,
        student_id: uuid.UUID,
        date: dt_date,
        *,
        default_status: str,
    ) -> StudentAttendance:
        existing = self.get_by_student_date(student_id, date)
        if existing:
            return existing
        row = StudentAttendance(
            student_id=student_id,
            date=date,
            status=default_status,
            verified=False,
            verified_at=None,
            verified_by=None,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def upsert_from_gate(
        self,
        *,
        student_id: uuid.UUID,
        date: dt_date,
        direction: str,
        gate_attendance_id: uuid.UUID,
        computed_status: str,
    ) -> StudentAttendance:
        row = self.get_or_create(
            student_id,
            date,
            default_status=computed_status,
        )

        direction_upper = direction.upper()
        if direction_upper == "IN":
            row.checkin_id = gate_attendance_id
            row.status = computed_status
        elif direction_upper == "OUT":
            row.checkout_id = gate_attendance_id
            if row.status in {
                "IZIN_SAKIT",
                "IZIN_ACARA_KELUARGA",
                "IZIN_ACARA_KEAGAMAAN",
            }:
                row.status = computed_status
                row.verified = False
                row.verified_at = None
                row.verified_by = None
        else:
            raise ValueError("invalid direction")

        self.db.add(row)
        self.db.flush()
        return row

    def backfill_from_gate_attendance(
        self,
        *,
        date_from: dt_date,
        date_to: dt_date,
        gate_in_time: dt_time,
    ) -> None:
        stmt = (
            select(GateAttendance)
            .where(
                GateAttendance.date >= date_from,
                GateAttendance.date <= date_to,
            )
            .order_by(GateAttendance.date.asc())
        )
        gates = list(self.db.execute(stmt).scalars().all())
        for g in gates:
            if g.direction.upper() == "IN":
                computed_status = (
                    "TELAT" if g.time > gate_in_time else "TEPAT_WAKTU"
                )
            else:
                computed_status = "TEPAT_WAKTU"
            self.upsert_from_gate(
                student_id=g.student_id,
                date=g.date,
                direction=g.direction,
                gate_attendance_id=g.id,
                computed_status=computed_status,
            )

    def build_list_stmt(
        self,
        *,
        date_from: dt_date,
        date_to: dt_date,
        q: str | None,
        class_instance_id: uuid.UUID | None,
        status: str | None,
    ) -> Select:
        from app.models.class_instances import ClassInstance
        from app.models.classes import Class
        from app.models.enrollments import StudentClassEnrollment
        from app.models.students import Student
        from app.models.users import User

        stmt = (
            select(StudentAttendance)
            .join(Student, Student.id == StudentAttendance.student_id)
            .outerjoin(
                StudentClassEnrollment,
                StudentClassEnrollment.student_id == Student.id,
            )
            .outerjoin(
                ClassInstance,
                ClassInstance.id == StudentClassEnrollment.class_instance_id,
            )
            .outerjoin(Class, Class.id == ClassInstance.class_id)
            .outerjoin(User, User.id == StudentAttendance.verified_by)
            .where(
                StudentAttendance.date >= date_from,
                StudentAttendance.date <= date_to,
            )
        )

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    Student.name.ilike(like),
                    Student.nis.ilike(like),
                )
            )

        if class_instance_id:
            stmt = stmt.where(ClassInstance.id == class_instance_id)

        if status:
            stmt = stmt.where(StudentAttendance.status == status)

        return stmt
