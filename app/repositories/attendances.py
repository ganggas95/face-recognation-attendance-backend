from __future__ import annotations

import uuid
from datetime import date as dt_date

from app.models import Attendance, ClassInstance, ClassSubjectSchedule, Student
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload


class AttendanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, attendance: Attendance) -> None:
        self.db.add(attendance)

    def get_by_student_schedule_date(
        self,
        *,
        student_id: uuid.UUID,
        schedule_id: uuid.UUID,
        date: dt_date,
    ) -> Attendance | None:
        stmt = select(Attendance).where(
            Attendance.student_id == student_id,
            Attendance.schedule_id == schedule_id,
            Attendance.date == date,
        )
        return self.db.scalar(stmt)

    def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
        class_instance_id: uuid.UUID | None = None,
        subject_id: uuid.UUID | None = None,
        teacher_id: uuid.UUID | None = None,
        date: dt_date | None = None,
        student_name: str | None = None,
    ) -> tuple[list[Attendance], int]:
        stmt = (
            select(Attendance)
            .join(Attendance.student)
            .join(Attendance.schedule)
            .join(ClassSubjectSchedule.class_instance)
            .join(ClassInstance.class_template)
            .join(ClassSubjectSchedule.subject)
            .join(ClassSubjectSchedule.teacher)
        )

        total_stmt = (
            select(func.count())
            .select_from(Attendance)
            .join(Attendance.student)
            .join(Attendance.schedule)
            .join(ClassSubjectSchedule.class_instance)
            .join(ClassInstance.class_template)
            .join(ClassSubjectSchedule.subject)
            .join(ClassSubjectSchedule.teacher)
        )

        if class_instance_id is not None:
            stmt = stmt.where(
                ClassSubjectSchedule.class_instance_id == class_instance_id
            )
            total_stmt = total_stmt.where(
                ClassSubjectSchedule.class_instance_id == class_instance_id
            )

        if subject_id is not None:
            stmt = stmt.where(ClassSubjectSchedule.subject_id == subject_id)
            total_stmt = total_stmt.where(
                ClassSubjectSchedule.subject_id == subject_id
            )

        if teacher_id is not None:
            stmt = stmt.where(ClassSubjectSchedule.teacher_id == teacher_id)
            total_stmt = total_stmt.where(
                ClassSubjectSchedule.teacher_id == teacher_id
            )

        if date is not None:
            stmt = stmt.where(Attendance.date == date)
            total_stmt = total_stmt.where(Attendance.date == date)

        if student_name:
            q = student_name.strip()
            if q:
                like = f"%{q}%"
                stmt = stmt.where(Student.name.ilike(like))
                total_stmt = total_stmt.where(Student.name.ilike(like))

        total = int(self.db.scalar(total_stmt) or 0)
        stmt = (
            stmt.options(
                joinedload(Attendance.student),
                joinedload(Attendance.schedule).joinedload(
                    ClassSubjectSchedule.subject
                ),
                joinedload(Attendance.schedule)
                .joinedload(ClassSubjectSchedule.teacher),
                joinedload(Attendance.schedule)
                .joinedload(ClassSubjectSchedule.class_instance)
                .joinedload(ClassInstance.class_template),
            )
            .order_by(
                Attendance.date.desc(),
                Attendance.time.desc(),
                Attendance.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt).unique())
        return items, total
